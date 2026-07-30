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
        existing = await project_repo.get_by_code(db, project_code=obj_in.project_code, tenant_id=tenant_id)
        if existing:
            raise DuplicateProjectCode(f"Project code '{obj_in.project_code}' already exists in this tenant.")

        project = await project_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ProjectService: Created project '{project.project_code}' (ID: {project.id})")
        return project

    async def get_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Project:
        """Fetch project by ID or raise ProjectNotFound."""
        project = await project_repo.get_by_id(
            db, id=project_id, tenant_id=tenant_id, include_details=include_details
        )
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

        updated_project = await project_repo.update(
            db, db_obj=project, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"ProjectService: Updated project {project_id}")
        return updated_project

    async def archive_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user: User
    ) -> Project:
        """Archive a project."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        if project.is_archived:
            return project

        archived = await project_repo.archive(
            db, project_id=project_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ProjectService: Archived project {project_id}")
        return archived

    async def restore_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user: User
    ) -> Project:
        """Restore an archived project."""
        project = await self.get_project(db, project_id=project_id, tenant_id=tenant_id)
        if not project.is_archived:
            return project

        restored = await project_repo.restore(
            db, project_id=project_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ProjectService: Restored project {project_id}")
        return restored

    async def delete_project(
        self, db: AsyncSession, *, project_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete a project."""
        success = await project_repo.soft_delete(
            db, id=project_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise ProjectNotFound(f"Project {project_id} not found.")
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
        return await project_repo.list_projects(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

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
