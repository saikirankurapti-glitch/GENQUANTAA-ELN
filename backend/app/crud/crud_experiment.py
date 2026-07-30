import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentAttachment, ExperimentCollaborator
from app.schemas.experiment import ExperimentCreate, ExperimentFilter, ExperimentPagination, ExperimentUpdate

logger = logging.getLogger(__name__)


class ExperimentRepository:
    """Async Repository handling data access for Experiment entities with strict tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
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
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(exp)
        await db.commit()
        await db.refresh(exp)
        return exp

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Experiment]:
        """Fetch Experiment by ID within tenant scope."""
        stmt = select(Experiment).where(
            Experiment.id == id,
            Experiment.tenant_id == tenant_id,
            Experiment.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(Experiment.collaborators),
                selectinload(Experiment.attachments),
                selectinload(Experiment.project),
                selectinload(Experiment.owner),
                selectinload(Experiment.reviewer),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, project_id: UUID, experiment_code: str, tenant_id: UUID
    ) -> Optional[Experiment]:
        """Fetch Experiment by experiment_code within project and tenant scope."""
        stmt = select(Experiment).where(
            Experiment.project_id == project_id,
            Experiment.experiment_code == experiment_code.upper(),
            Experiment.tenant_id == tenant_id,
            Experiment.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Experiment,
        obj_in: ExperimentUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Experiment:
        """Update existing Experiment attributes."""
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
        self, db: AsyncSession, *, experiment_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Experiment]:
        """Archive an Experiment."""
        exp = await self.get_by_id(db, id=experiment_id, tenant_id=tenant_id)
        if not exp:
            return None

        exp.is_archived = True
        exp.archived_at = datetime.now(timezone.utc)
        exp.status = ExperimentStatus.ARCHIVED
        exp.updated_by = current_user_id
        db.add(exp)
        await db.commit()
        await db.refresh(exp)
        return exp

    async def restore(
        self, db: AsyncSession, *, experiment_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Experiment]:
        """Restore an archived Experiment back to IN_PROGRESS or DRAFT."""
        exp = await self.get_by_id(db, id=experiment_id, tenant_id=tenant_id)
        if not exp:
            return None

        exp.is_archived = False
        exp.archived_at = None
        exp.status = ExperimentStatus.IN_PROGRESS
        exp.updated_by = current_user_id
        db.add(exp)
        await db.commit()
        await db.refresh(exp)
        return exp

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete an Experiment."""
        exp = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not exp:
            return False

        exp.is_deleted = True
        exp.deleted_at = datetime.now(timezone.utc)
        exp.deleted_by = current_user_id
        db.add(exp)
        await db.commit()
        return True

    async def list_experiments(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: ExperimentFilter,
        pagination: ExperimentPagination
    ) -> Tuple[List[Experiment], int]:
        """List and search Experiments with filtering and pagination."""
        query = select(Experiment).where(
            Experiment.tenant_id == tenant_id,
            Experiment.is_deleted == False
        )

        if filter_params.project_id:
            query = query.where(Experiment.project_id == filter_params.project_id)
        if filter_params.status:
            query = query.where(Experiment.status == filter_params.status)
        if filter_params.priority:
            query = query.where(Experiment.priority == filter_params.priority)
        if filter_params.owner_id:
            query = query.where(Experiment.owner_id == filter_params.owner_id)
        if filter_params.is_archived is not None:
            query = query.where(Experiment.is_archived == filter_params.is_archived)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    Experiment.experiment_code.ilike(pattern),
                    Experiment.title.ilike(pattern),
                    Experiment.description.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(Experiment, pagination.sort_by, Experiment.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def list_by_project(
        self, db: AsyncSession, *, tenant_id: UUID, project_id: UUID, pagination: ExperimentPagination
    ) -> Tuple[List[Experiment], int]:
        """List experiments scoped to a specific project."""
        filter_params = ExperimentFilter(project_id=project_id)
        return await self.list_experiments(db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination)

    async def list_by_owner(
        self, db: AsyncSession, *, tenant_id: UUID, owner_id: UUID, pagination: ExperimentPagination
    ) -> Tuple[List[Experiment], int]:
        """List experiments owned by a specific scientist."""
        filter_params = ExperimentFilter(owner_id=owner_id)
        return await self.list_experiments(db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination)

    async def add_collaborator(
        self,
        db: AsyncSession,
        *,
        experiment_id: UUID,
        user_id: UUID,
        role: str = "editor",
        added_by: Optional[UUID] = None
    ) -> ExperimentCollaborator:
        """Add a collaborator to an experiment."""
        collab = ExperimentCollaborator(
            experiment_id=experiment_id,
            user_id=user_id,
            role=role,
            added_by=added_by,
        )
        db.add(collab)
        await db.commit()
        await db.refresh(collab)
        return collab


experiment_repo = ExperimentRepository()
