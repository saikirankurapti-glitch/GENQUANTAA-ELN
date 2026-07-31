import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import ExperimentStatus, ProjectStatus
from app.models.compliance import AuditLog
from app.models.dashboard import Notification
from app.models.identity import User
from app.models.project import Project
from app.models.experiment import Experiment
from app.models.research import Study

logger = logging.getLogger(__name__)


class DashboardRepository:
    """Repository handling data access queries for the aggregated Dashboard view."""

    async def get_project_count(self, db: AsyncSession, *, tenant_id: UUID) -> int:
        """Count active non-deleted projects for tenant."""
        return await Project.find(Project.tenant_id == tenant_id, Project.is_deleted != True).count()

    async def get_experiment_counts(self, db: AsyncSession, *, tenant_id: UUID) -> Tuple[int, int]:
        """
        Count active vs completed experiments within tenant scope.
        Returns (active_count, completed_count).
        """
        active_statuses = [ExperimentStatus.DRAFT, ExperimentStatus.IN_PROGRESS, ExperimentStatus.SUBMITTED]
        from beanie.operators import In
        active_count = await Experiment.find(
            Experiment.tenant_id == tenant_id, 
            Experiment.is_deleted != True, 
            In(Experiment.status, active_statuses)
        ).count()

        completed_statuses = [ExperimentStatus.APPROVED, ExperimentStatus.COMPLETED, ExperimentStatus.ARCHIVED]
        completed_count = await Experiment.find(
            Experiment.tenant_id == tenant_id, 
            Experiment.is_deleted != True, 
            In(Experiment.status, completed_statuses)
        ).count()

        return active_count, completed_count

    async def get_recent_experiments(
        self, db: AsyncSession, *, tenant_id: UUID, limit: int = 5
    ) -> List[Experiment]:
        """Fetch top N recent experiments within tenant."""
        return await Experiment.find(
            Experiment.tenant_id == tenant_id, 
            Experiment.is_deleted != True
        ).sort("-updated_at").limit(limit).to_list()

    async def get_pending_notifications(
        self, db: AsyncSession, *, tenant_id: UUID, user_id: UUID, limit: int = 5
    ) -> List[Notification]:
        """Fetch unread notifications for specified user."""
        stmt = (
            select(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_activity_feed(
        self, db: AsyncSession, *, limit: int = 10
    ) -> List[Tuple[AuditLog, Optional[str]]]:
        """Fetch recent platform audit logs with user names."""
        stmt = (
            select(AuditLog, User.first_name, User.last_name)
            .outerjoin(User, AuditLog.performed_by == User.id)
            .order_by(AuditLog.performed_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        results = []
        for row in res.all():
            audit_log = row[0]
            first_name = row[1] or ""
            last_name = row[2] or ""
            user_name = f"{first_name} {last_name}".strip() or "System"
            results.append((audit_log, user_name))
        return results


dashboard_repo = DashboardRepository()
