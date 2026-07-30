import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectCollaborator, ProjectAttachment
from app.schemas.project import ProjectCreate, ProjectFilter, ProjectPagination, ProjectUpdate
from app.db.enums import ProjectStatus

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Async Repository handling data access for Project entities with strict tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ProjectCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Project:
        """Create a new Project record."""
        project = Project(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            owner_id=obj_in.owner_id or current_user_id,
            project_code=obj_in.project_code,
            name=obj_in.name,
            description=obj_in.description,
            objective=obj_in.objective,
            status=obj_in.status,
            priority=obj_in.priority,
            tags=obj_in.tags,
            visibility=obj_in.visibility,
            start_date=obj_in.start_date,
            target_end_date=obj_in.target_end_date,
            metadata_json=obj_in.metadata_json,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Project]:
        """Fetch Project by ID within tenant scope."""
        stmt = select(Project).where(
            Project.id == id,
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(Project.collaborators),
                selectinload(Project.attachments),
                selectinload(Project.organization),
                selectinload(Project.owner),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, project_code: str, tenant_id: UUID
    ) -> Optional[Project]:
        """Fetch Project by unique project_code within tenant scope."""
        stmt = select(Project).where(
            Project.project_code == project_code.upper(),
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Project,
        obj_in: ProjectUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Project:
        """Update existing Project attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def archive(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Project]:
        """Archive a Project."""
        project = await self.get_by_id(db, id=project_id, tenant_id=tenant_id)
        if not project:
            return None

        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)
        project.status = ProjectStatus.ARCHIVED
        project.updated_by = current_user_id
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def restore(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Project]:
        """Restore an archived Project."""
        project = await self.get_by_id(db, id=project_id, tenant_id=tenant_id)
        if not project:
            return None

        project.is_archived = False
        project.archived_at = None
        project.status = ProjectStatus.ACTIVE
        project.updated_by = current_user_id
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete Project while preserving audit history."""
        project = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not project:
            return False

        project.is_deleted = True
        project.deleted_at = datetime.now(timezone.utc)
        project.deleted_by = current_user_id
        db.add(project)
        await db.commit()
        return True

    async def list_projects(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: ProjectFilter,
        pagination: ProjectPagination
    ) -> Tuple[List[Project], int]:
        """List and search Projects with pagination and filtering."""
        query = select(Project).where(
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        )

        # Filters
        if filter_params.status:
            query = query.where(Project.status == filter_params.status)
        if filter_params.priority:
            query = query.where(Project.priority == filter_params.priority)
        if filter_params.owner_id:
            query = query.where(Project.owner_id == filter_params.owner_id)
        if filter_params.is_archived is not None:
            query = query.where(Project.is_archived == filter_params.is_archived)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    Project.project_code.ilike(pattern),
                    Project.name.ilike(pattern),
                    Project.description.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(Project, pagination.sort_by, Project.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def list_by_owner(
        self, db: AsyncSession, *, tenant_id: UUID, owner_id: UUID, pagination: ProjectPagination
    ) -> Tuple[List[Project], int]:
        """List Projects owned by a specific user."""
        filter_params = ProjectFilter(owner_id=owner_id)
        return await self.list_projects(db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination)

    async def list_by_collaborator(
        self, db: AsyncSession, *, tenant_id: UUID, user_id: UUID, pagination: ProjectPagination
    ) -> Tuple[List[Project], int]:
        """List Projects where specified user is an assigned collaborator."""
        query = (
            select(Project)
            .join(ProjectCollaborator, Project.id == ProjectCollaborator.project_id)
            .where(
                Project.tenant_id == tenant_id,
                ProjectCollaborator.user_id == user_id,
                Project.is_deleted == False,
            )
        )

        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        offset = (pagination.page - 1) * pagination.page_size
        query = query.order_by(Project.created_at.desc()).offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def add_collaborator(
        self,
        db: AsyncSession,
        *,
        project_id: UUID,
        user_id: UUID,
        role: str = "viewer",
        added_by: Optional[UUID] = None
    ) -> ProjectCollaborator:
        """Add a collaborator to a project."""
        collaborator = ProjectCollaborator(
            project_id=project_id,
            user_id=user_id,
            role=role,
            added_by=added_by,
        )
        db.add(collaborator)
        await db.commit()
        await db.refresh(collaborator)
        return collaborator

    async def remove_collaborator(self, db: AsyncSession, *, project_id: UUID, user_id: UUID) -> bool:
        """Remove a collaborator from a project."""
        stmt = select(ProjectCollaborator).where(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == user_id,
        )
        res = await db.execute(stmt)
        collab = res.scalar_one_or_none()
        if not collab:
            return False
        await db.delete(collab)
        await db.commit()
        return True


project_repo = ProjectRepository()
