import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_experiment import experiment_repo
from app.crud.crud_project import project_repo
from app.db.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentCollaborator
from app.models.identity import User
from app.schemas.experiment import ExperimentCreate, ExperimentFilter, ExperimentPagination, ExperimentUpdate

logger = logging.getLogger(__name__)


# Domain Exceptions
class ExperimentNotFound(Exception):
    pass


class DuplicateExperimentCode(Exception):
    pass


class ProjectArchivedOrNotFound(Exception):
    pass


class ExperimentArchivedError(Exception):
    pass


class InvalidExperimentStatusTransition(Exception):
    pass


VALID_EXPERIMENT_TRANSITIONS = {
    ExperimentStatus.DRAFT: {ExperimentStatus.PLANNED, ExperimentStatus.IN_PROGRESS, ExperimentStatus.CANCELLED},
    ExperimentStatus.PLANNED: {ExperimentStatus.IN_PROGRESS, ExperimentStatus.CANCELLED},
    ExperimentStatus.IN_PROGRESS: {ExperimentStatus.SUBMITTED, ExperimentStatus.IN_REVIEW, ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED},
    ExperimentStatus.SUBMITTED: {ExperimentStatus.IN_REVIEW, ExperimentStatus.APPROVED, ExperimentStatus.REJECTED},
    ExperimentStatus.IN_REVIEW: {ExperimentStatus.APPROVED, ExperimentStatus.REJECTED},
    ExperimentStatus.APPROVED: {ExperimentStatus.COMPLETED, ExperimentStatus.ARCHIVED},
    ExperimentStatus.COMPLETED: {ExperimentStatus.ARCHIVED, ExperimentStatus.IN_PROGRESS},
    ExperimentStatus.REJECTED: {ExperimentStatus.IN_PROGRESS, ExperimentStatus.CANCELLED},
    ExperimentStatus.CANCELLED: {ExperimentStatus.DRAFT, ExperimentStatus.ARCHIVED},
    ExperimentStatus.ARCHIVED: {ExperimentStatus.IN_PROGRESS},
}


class ExperimentService:
    """Service layer enforcing experiment lifecycle rules, project containment, and state machine transitions."""

    def validate_status_transition(self, current_status: ExperimentStatus, new_status: ExperimentStatus) -> None:
        """Enforce valid state machine transitions for experiment status."""
        if current_status == new_status:
            return
        allowed = VALID_EXPERIMENT_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidExperimentStatusTransition(
                f"Invalid experiment status transition from '{current_status}' to '{new_status}'."
            )

    async def create_experiment(
        self, db: AsyncSession, *, obj_in: ExperimentCreate, tenant_id: UUID, current_user: User
    ) -> Experiment:
        """Create a new experiment ensuring project exists, is active, and code is unique."""
        # 1. Validate Parent Project
        project = await project_repo.get_by_id(db, id=obj_in.project_id, tenant_id=tenant_id)
        if not project:
            raise ProjectArchivedOrNotFound(f"Parent Project {obj_in.project_id} not found in this tenant.")
        if project.is_archived:
            raise ProjectArchivedOrNotFound("Cannot create an experiment inside an archived Project.")

        # 2. Validate Code Uniqueness within Project
        existing = await experiment_repo.get_by_code(
            db, project_id=obj_in.project_id, experiment_code=obj_in.experiment_code, tenant_id=tenant_id
        )
        if existing:
            raise DuplicateExperimentCode(
                f"Experiment code '{obj_in.experiment_code}' already exists in Project {obj_in.project_id}."
            )

        exp = await experiment_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ExperimentService: Created experiment '{exp.experiment_code}' (ID: {exp.id})")
        return exp

    async def get_experiment(
        self, db: AsyncSession, *, experiment_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Experiment:
        """Fetch experiment by ID or raise ExperimentNotFound."""
        exp = await experiment_repo.get_by_id(
            db, id=experiment_id, tenant_id=tenant_id, include_details=include_details
        )
        if not exp:
            raise ExperimentNotFound(f"Experiment {experiment_id} not found.")
        return exp

    async def update_experiment(
        self,
        db: AsyncSession,
        *,
        experiment_id: UUID,
        obj_in: ExperimentUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Experiment:
        """Update experiment ensuring non-archived state and valid status transition."""
        exp = await self.get_experiment(db, experiment_id=experiment_id, tenant_id=tenant_id)
        if exp.is_archived:
            raise ExperimentArchivedError("Cannot update an archived experiment. Restore it first.")

        if obj_in.status and obj_in.status != exp.status:
            self.validate_status_transition(exp.status, obj_in.status)

        updated_exp = await experiment_repo.update(
            db, db_obj=exp, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"ExperimentService: Updated experiment {experiment_id}")
        return updated_exp

    async def archive_experiment(
        self, db: AsyncSession, *, experiment_id: UUID, tenant_id: UUID, current_user: User
    ) -> Experiment:
        """Archive an experiment."""
        exp = await self.get_experiment(db, experiment_id=experiment_id, tenant_id=tenant_id)
        if exp.is_archived:
            return exp

        archived = await experiment_repo.archive(
            db, experiment_id=experiment_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ExperimentService: Archived experiment {experiment_id}")
        return archived

    async def restore_experiment(
        self, db: AsyncSession, *, experiment_id: UUID, tenant_id: UUID, current_user: User
    ) -> Experiment:
        """Restore an archived experiment."""
        exp = await self.get_experiment(db, experiment_id=experiment_id, tenant_id=tenant_id)
        if not exp.is_archived:
            return exp

        restored = await experiment_repo.restore(
            db, experiment_id=experiment_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ExperimentService: Restored experiment {experiment_id}")
        return restored

    async def delete_experiment(
        self, db: AsyncSession, *, experiment_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete an experiment."""
        success = await experiment_repo.soft_delete(
            db, id=experiment_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise ExperimentNotFound(f"Experiment {experiment_id} not found.")
        logger.info(f"ExperimentService: Soft deleted experiment {experiment_id}")
        return True

    async def list_experiments(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: ExperimentFilter,
        pagination: ExperimentPagination
    ) -> Tuple[List[Experiment], int]:
        """List experiments with filtering and pagination."""
        return await experiment_repo.list_experiments(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

    async def add_collaborator(
        self,
        db: AsyncSession,
        *,
        experiment_id: UUID,
        user_id: UUID,
        role: str,
        tenant_id: UUID,
        current_user: User
    ) -> ExperimentCollaborator:
        """Add a collaborator to an experiment."""
        exp = await self.get_experiment(db, experiment_id=experiment_id, tenant_id=tenant_id)
        if exp.is_archived:
            raise ExperimentArchivedError("Cannot modify collaborators on an archived experiment.")

        return await experiment_repo.add_collaborator(
            db, experiment_id=experiment_id, user_id=user_id, role=role, added_by=current_user.id
        )


experiment_service = ExperimentService()
