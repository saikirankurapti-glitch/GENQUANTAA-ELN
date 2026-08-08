import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from uuid import UUID

from app.db.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentAttachment, ExperimentCollaborator
from app.schemas.experiment import ExperimentCreate, ExperimentFilter, ExperimentPagination, ExperimentUpdate

logger = logging.getLogger(__name__)


class ExperimentRepository:
    """Async Repository handling data access for Experiment entities with strict tenant isolation."""

    async def create(
        self,
        *,
        obj_in: ExperimentCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Experiment:
        """Create a new Experiment record."""
        exp = Experiment(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            project_id=obj_in.project_id,
            protocol_id=obj_in.protocol_id,
            owner_id=obj_in.owner_id or current_user_id,
            reviewer_id=obj_in.reviewer_id,
            experiment_code=obj_in.experiment_code,
            title=obj_in.title,
            objective=obj_in.objective,
            hypothesis=obj_in.hypothesis,
            description=obj_in.description,
            status=obj_in.status,
            priority=obj_in.priority,
            start_date=obj_in.start_date,
            planned_end_date=obj_in.planned_end_date,
            metadata_json=obj_in.metadata_json,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await exp.insert()
        return exp

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Experiment]:
        """Fetch Experiment by ID within tenant scope."""
        exp = await Experiment.find_one(
            Experiment.id == id,
            Experiment.tenant_id == tenant_id,
            Experiment.is_deleted == False
        )
        return exp

    async def get_by_code(
        self, *, project_id: UUID, experiment_code: str, tenant_id: UUID
    ) -> Optional[Experiment]:
        """Fetch Experiment by experiment_code within project and tenant scope."""
        exp = await Experiment.find_one(
            Experiment.project_id == project_id,
            Experiment.experiment_code == experiment_code.upper(),
            Experiment.tenant_id == tenant_id,
            Experiment.is_deleted == False
        )
        return exp

    async def update(
        self,
        *,
        db_obj: Experiment,
        obj_in: ExperimentUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Experiment:
        """Update existing Experiment attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()
        return db_obj

    async def archive(
        self, *, experiment_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Experiment]:
        """Archive an Experiment."""
        exp = await self.get_by_id(id=experiment_id, tenant_id=tenant_id)
        if not exp:
            return None

        exp.is_archived = True
        exp.archived_at = datetime.now(timezone.utc)
        exp.status = ExperimentStatus.ARCHIVED
        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        return exp

    async def restore(
        self, *, experiment_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Experiment]:
        """Restore an archived Experiment back to IN_PROGRESS or DRAFT."""
        exp = await self.get_by_id(id=experiment_id, tenant_id=tenant_id)
        if not exp:
            return None

        exp.is_archived = False
        exp.archived_at = None
        exp.status = ExperimentStatus.IN_PROGRESS
        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        return exp

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete an Experiment."""
        exp = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not exp:
            return False

        exp.is_deleted = True
        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        return True

    async def list_experiments(
        self,
        *,
        tenant_id: UUID,
        filter_params: ExperimentFilter,
        pagination: ExperimentPagination
    ) -> Tuple[List[dict], int]:
        """List and search Experiments with filtering and pagination."""
        query = Experiment.find(
            Experiment.tenant_id == tenant_id,
            Experiment.is_deleted == False
        )

        if filter_params.project_id:
            query = query.find(Experiment.project_id == filter_params.project_id)
        if filter_params.status:
            query = query.find(Experiment.status == filter_params.status)
        if filter_params.priority:
            query = query.find(Experiment.priority == filter_params.priority)
        if filter_params.owner_id:
            query = query.find(Experiment.owner_id == filter_params.owner_id)
        if filter_params.is_archived is not None:
            query = query.find(Experiment.is_archived == filter_params.is_archived)
        if filter_params.search:
            query = query.find({"$or": [
                {"experiment_code": {"$regex": filter_params.search, "$options": "i"}},
                {"title": {"$regex": filter_params.search, "$options": "i"}},
                {"description": {"$regex": filter_params.search, "$options": "i"}},
            ]})

        total = await query.count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await query.sort(-Experiment.created_at).skip(skip).limit(pagination.page_size).to_list()
        
        mapped_items = []
        for i in items:
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": i.organization_id,
                "project_id": i.project_id,
                "owner_id": i.owner_id,
                "reviewer_id": i.reviewer_id,
                "experiment_code": i.experiment_code,
                "title": i.title,
                "objective": i.objective,
                "hypothesis": i.hypothesis,
                "description": i.description,
                "status": i.status.value if hasattr(i.status, 'value') else str(i.status),
                "priority": i.priority,
                "protocol_id": i.protocol_id,
                "start_date": i.start_date,
                "planned_end_date": i.planned_end_date,
                "completed_date": getattr(i, 'completed_date', None),
                "reviewed_date": getattr(i, 'reviewed_date', None),
                "is_archived": i.is_archived,
                "archived_at": i.archived_at,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            })
            
        return mapped_items, total

    async def list_by_project(
        self, *, tenant_id: UUID, project_id: UUID, pagination: ExperimentPagination
    ) -> Tuple[List[dict], int]:
        """List experiments scoped to a specific project."""
        filter_params = ExperimentFilter(project_id=project_id)
        return await self.list_experiments(tenant_id=tenant_id, filter_params=filter_params, pagination=pagination)

    async def list_by_owner(
        self, *, tenant_id: UUID, owner_id: UUID, pagination: ExperimentPagination
    ) -> Tuple[List[dict], int]:
        """List experiments owned by a specific scientist."""
        filter_params = ExperimentFilter(owner_id=owner_id)
        return await self.list_experiments(tenant_id=tenant_id, filter_params=filter_params, pagination=pagination)

    async def add_collaborator(
        self,
        *,
        experiment_id: UUID,
        user_id: UUID,
        role: str = "editor",
        tenant_id: UUID,
        added_by: Optional[UUID] = None
    ) -> ExperimentCollaborator:
        """Add a collaborator to an experiment."""
        collab = ExperimentCollaborator(
            experiment_id=experiment_id,
            user_id=user_id,
            role=role,
            tenant_id=tenant_id,
        )
        await collab.insert()
        return collab


experiment_repo = ExperimentRepository()
