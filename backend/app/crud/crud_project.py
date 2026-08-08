import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from uuid import UUID

from app.models.project import Project, ProjectCollaborator, ProjectAttachment
from app.schemas.project import ProjectCreate, ProjectFilter, ProjectPagination, ProjectUpdate
from app.db.enums import ProjectStatus

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Async Repository handling data access for Project entities with strict tenant isolation."""

    async def create(
        self,
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await project.insert()
        return project

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Project]:
        """Fetch Project by ID within tenant scope."""
        project = await Project.find_one(
            Project.id == id,
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        )
        return project

    async def get_by_code(
        self, *, project_code: str, tenant_id: UUID
    ) -> Optional[Project]:
        """Fetch Project by unique project_code within tenant scope."""
        project = await Project.find_one(
            Project.project_code == project_code.upper(),
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        )
        return project

    async def update(
        self,
        *,
        db_obj: Project,
        obj_in: ProjectUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Project:
        """Update existing Project attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()
        return db_obj

    async def archive(
        self, *, project_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Project]:
        """Archive a Project."""
        project = await self.get_by_id(id=project_id, tenant_id=tenant_id)
        if not project:
            return None

        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)
        project.status = ProjectStatus.ARCHIVED
        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        return project

    async def restore(
        self, *, project_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Project]:
        """Restore an archived Project."""
        project = await self.get_by_id(id=project_id, tenant_id=tenant_id)
        if not project:
            return None

        project.is_archived = False
        project.archived_at = None
        project.status = ProjectStatus.ACTIVE
        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        return project

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete Project while preserving audit history."""
        project = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not project:
            return False

        project.is_deleted = True
        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        return True

    async def list_projects(
        self,
        *,
        tenant_id: UUID,
        filter_params: ProjectFilter,
        pagination: ProjectPagination
    ) -> Tuple[List[dict], int]:
        """List and search Projects with pagination and filtering."""
        query = Project.find(
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        )

        # Filters
        if filter_params.status:
            query = query.find(Project.status == filter_params.status)
        if filter_params.priority:
            query = query.find(Project.priority == filter_params.priority)
        if filter_params.owner_id:
            query = query.find(Project.owner_id == filter_params.owner_id)
        if filter_params.is_archived is not None:
            query = query.find(Project.is_archived == filter_params.is_archived)
        if filter_params.search:
            query = query.find({"$or": [
                {"project_code": {"$regex": filter_params.search, "$options": "i"}},
                {"name": {"$regex": filter_params.search, "$options": "i"}},
                {"description": {"$regex": filter_params.search, "$options": "i"}},
            ]})

        total = await query.count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await query.sort(-Project.created_at).skip(skip).limit(pagination.page_size).to_list()
        
        mapped_items = []
        for i in items:
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": i.organization_id,
                "owner_id": i.owner_id,
                "name": i.name,
                "project_code": i.project_code,
                "description": i.description,
                "objective": i.objective,
                "status": i.status.value if hasattr(i.status, 'value') else str(i.status),
                "priority": i.priority,
                "tags": i.tags,
                "visibility": i.visibility,
                "is_archived": i.is_archived,
                "start_date": i.start_date,
                "target_end_date": i.target_end_date,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            })

        return mapped_items, total

    async def list_by_owner(
        self, *, tenant_id: UUID, owner_id: UUID, pagination: ProjectPagination
    ) -> Tuple[List[dict], int]:
        """List Projects owned by a specific user."""
        filter_params = ProjectFilter(owner_id=owner_id)
        return await self.list_projects(tenant_id=tenant_id, filter_params=filter_params, pagination=pagination)

    async def list_by_collaborator(
        self, *, tenant_id: UUID, user_id: UUID, pagination: ProjectPagination
    ) -> Tuple[List[dict], int]:
        """List Projects where specified user is an assigned collaborator."""
        collaborations = await ProjectCollaborator.find(
            ProjectCollaborator.user_id == user_id,
            ProjectCollaborator.tenant_id == tenant_id
        ).to_list()
        
        project_ids = [c.project_id for c in collaborations]
        if not project_ids:
            return [], 0
            
        query = Project.find(
            {"_id": {"$in": project_ids}},
            Project.is_deleted == False
        )
        total = await query.count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await query.sort(-Project.created_at).skip(skip).limit(pagination.page_size).to_list()
        
        mapped_items = []
        for i in items:
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": i.organization_id,
                "owner_id": i.owner_id,
                "name": i.name,
                "project_code": i.project_code,
                "description": i.description,
                "objective": i.objective,
                "status": i.status.value if hasattr(i.status, 'value') else str(i.status),
                "priority": i.priority,
                "tags": i.tags,
                "visibility": i.visibility,
                "is_archived": i.is_archived,
                "start_date": i.start_date,
                "target_end_date": i.target_end_date,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            })

        return mapped_items, total

    async def add_collaborator(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        role: str = "viewer",
        tenant_id: UUID,
        added_by: Optional[UUID] = None
    ) -> ProjectCollaborator:
        """Add a collaborator to a project."""
        collaborator = ProjectCollaborator(
            project_id=project_id,
            user_id=user_id,
            role=role,
            tenant_id=tenant_id,
        )
        await collaborator.insert()
        return collaborator

    async def remove_collaborator(self, *, project_id: UUID, user_id: UUID) -> bool:
        """Remove a collaborator from a project."""
        collab = await ProjectCollaborator.find_one(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == user_id,
        )
        if not collab:
            return False
        await collab.delete()
        return True


project_repo = ProjectRepository()
