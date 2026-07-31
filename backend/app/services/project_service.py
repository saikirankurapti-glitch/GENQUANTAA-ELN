import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_project import project_repo
from app.db.enums import ProjectStatus
from app.models.identity import User
from app.models.project import Project, ProjectCollaborator
from app.schemas.project import ProjectCreate, ProjectFilter, ProjectPagination, ProjectUpdate

logger = logging.getLogger(__name__)


# Domain Exceptions
class ProjectNotFound(Exception):
    pass


class DuplicateProjectCode(Exception):
    pass


class ProjectArchivedError(Exception):
    pass


class ProjectPermissionDenied(Exception):
    pass


class InvalidStatusTransition(Exception):
    pass


VALID_TRANSITIONS = {
    ProjectStatus.PLANNED: {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED, ProjectStatus.ON_HOLD},
    ProjectStatus.ACTIVE: {ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED, ProjectStatus.ARCHIVED},
    ProjectStatus.ON_HOLD: {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
    ProjectStatus.COMPLETED: {ProjectStatus.ARCHIVED, ProjectStatus.ACTIVE},
    ProjectStatus.CANCELLED: {ProjectStatus.PLANNED, ProjectStatus.ARCHIVED},
    ProjectStatus.ARCHIVED: {ProjectStatus.ACTIVE},
}


class ProjectService:
    """Service layer enforcing project lifecycle rules, uniqueness, and collaborator rights."""

    def validate_status_transition(self, current_status: ProjectStatus, new_status: ProjectStatus) -> None:
        """Enforce valid state machine transitions for project status."""
        if current_status == new_status:
            return
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidStatusTransition(
                f"Invalid project status transition from '{current_status}' to '{new_status}'."
            )

    async def create_project(
        self, db: AsyncSession, *, obj_in: ProjectCreate, tenant_id: UUID, current_user: User
    ) -> Project:
        """Create a new project ensuring code uniqueness."""
        code = getattr(obj_in, "project_code", "PRJ-001")
        name = getattr(obj_in, "name", getattr(obj_in, "title", "New Project"))
        existing = await Project.find_one({"project_code": code, "tenant_id": tenant_id, "is_deleted": False})
        if existing:
            raise DuplicateProjectCode(f"Project code '{code}' already exists in this tenant.")

        project = Project(
            tenant_id=tenant_id,
            owner_id=current_user.id,
            name=name,
            project_code=code,
            description=obj_in.description,
            status=getattr(obj_in, "status", ProjectStatus.PLANNED),
            priority=getattr(obj_in, "priority", "MEDIUM"),
            tags=getattr(obj_in, "tags", []),
            visibility=getattr(obj_in, "visibility", "PRIVATE"),
            objective=getattr(obj_in, "objective", None),
            organization_id=getattr(obj_in, "organization_id", None),
            target_end_date=getattr(obj_in, "target_end_date", None),
            metadata_json=getattr(obj_in, "metadata_json", {})
        )
        await project.insert()
        logger.info(f"ProjectService: Created project '{project.project_code}' (ID: {project.id})")
        return project

    async def get_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Project:
        """Fetch project by ID or raise ProjectNotFound."""
        project = await Project.find_one({"_id": project_id, "tenant_id": tenant_id, "is_deleted": False})
        if not project:
            raise ProjectNotFound(f"Project {project_id} not found.")
        return project

    async def update_project(
        self,
        db: AsyncSession,
        *,
        project_id: UUID,
        obj_in: ProjectUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Project:
        """Update project ensuring non-archived status and valid transitions."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        if project.is_archived:
            raise ProjectArchivedError("Cannot update an archived project. Restore it first.")

        if obj_in.status and obj_in.status != project.status:
            self.validate_status_transition(project.status, obj_in.status)

        if obj_in.title or getattr(obj_in, "name", None):
            project.name = obj_in.title or getattr(obj_in, "name", project.name)
        if obj_in.description is not None:
            project.description = obj_in.description
        if obj_in.status is not None:
            project.status = obj_in.status

        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        logger.info(f"ProjectService: Updated project {project_id}")
        return project

    async def archive_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user: User
    ) -> Project:
        """Archive a project."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        if project.is_archived:
            return project

        project.is_archived = True
        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        logger.info(f"ProjectService: Archived project {project_id}")
        return project

    async def restore_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user: User
    ) -> Project:
        """Restore an archived project."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        if not project.is_archived:
            return project

        project.is_archived = False
        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        logger.info(f"ProjectService: Restored project {project_id}")
        return project

    async def delete_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete a project."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        project.is_deleted = True
        project.updated_at = datetime.now(timezone.utc)
        await project.save()
        logger.info(f"ProjectService: Soft deleted project {project_id}")
        return True

    async def list_projects(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: ProjectFilter,
        pagination: ProjectPagination
    ) -> Tuple[List[Project], int]:
        """List projects with filtering and pagination."""
        query_conditions = [
            Project.tenant_id == tenant_id,
            Project.is_deleted == False
        ]
        
        if filter_params and filter_params.search:
            from beanie.operators import RegEx
            query_conditions.append(RegEx(Project.name, filter_params.search, "i"))
            
        if filter_params and filter_params.status:
            query_conditions.append(Project.status == filter_params.status.value)
            
        total = await Project.find(*query_conditions).count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await Project.find(*query_conditions).skip(skip).limit(pagination.page_size).to_list()
        return items, total


    async def add_collaborator(
        self,
        db: AsyncSession,
        *,
        project_id: UUID,
        user_id: UUID,
        role: str,
        tenant_id: UUID,
        current_user: User
    ) -> ProjectCollaborator:
        """Add a collaborator to a project."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        if project.is_archived:
            raise ProjectArchivedError("Cannot modify collaborators on an archived project.")

        return await project_repo.add_collaborator(
            db, project_id=project_id, user_id=user_id, role=role, added_by=current_user.id
        )


project_service = ProjectService()
