import logging
from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.db.enums import ExperimentStatus, ProjectStatus
from app.models.identity import User
from app.models.project import Project, ProjectCollaborator
from app.models.experiment import Experiment, ExperimentCollaborator
from app.models.sample import Sample
from app.models.notebook import NotebookEntry
from app.schemas.dashboard import (
    NotificationSummary,
    ActivityFeedItem,
)

logger = logging.getLogger(__name__)

ACTIVE_EXP_STATUSES = [
    "draft", "planned", "in_progress", "submitted", "in_review",
    "DRAFT", "PLANNED", "IN_PROGRESS", "SUBMITTED", "IN_REVIEW",
    "Draft", "Planned", "In Progress", "Submitted", "In Review",
    ExperimentStatus.DRAFT, ExperimentStatus.PLANNED, ExperimentStatus.IN_PROGRESS,
    ExperimentStatus.SUBMITTED, ExperimentStatus.IN_REVIEW
]

COMPLETED_EXP_STATUSES = [
    "approved", "completed", "archived",
    "APPROVED", "COMPLETED", "ARCHIVED",
    "Approved", "Completed", "Archived",
    ExperimentStatus.APPROVED, ExperimentStatus.COMPLETED, ExperimentStatus.ARCHIVED
]

REVIEW_EXP_STATUSES = [
    "submitted", "in_review",
    "SUBMITTED", "IN_REVIEW",
    "Submitted", "In Review",
    ExperimentStatus.SUBMITTED, ExperimentStatus.IN_REVIEW
]

ACTIVE_PROJ_STATUSES = [
    "active", "planned", "on_hold",
    "ACTIVE", "PLANNED", "ON_HOLD",
    "Active", "Planned", "On Hold",
    ProjectStatus.ACTIVE, ProjectStatus.PLANNED, ProjectStatus.ON_HOLD
]


class DashboardRepository:
    """Repository handling data access queries for the aggregated Dashboard view."""

    async def get_project_count(self, *, tenant_id: UUID, user_id: Optional[UUID] = None) -> int:
        """
        Count active non-deleted projects for the user or tenant.
        Prioritizes user's projects/collaborations; falls back to tenant projects if 0.
        """
        if user_id:
            try:
                collab_projects = await ProjectCollaborator.find({"user_id": user_id}).to_list()
                collab_proj_ids = [cp.project_id for cp in collab_projects if hasattr(cp, "project_id")]

                user_proj_query = {
                    "tenant_id": tenant_id,
                    "is_deleted": {"$ne": True},
                    "status": {"$in": ACTIVE_PROJ_STATUSES},
                    "$or": [
                        {"owner_id": user_id},
                        {"_id": {"$in": collab_proj_ids}}
                    ]
                }
                user_count = await Project.find(user_proj_query).count()
                if user_count > 0:
                    return user_count
            except Exception as e:
                logger.warning(f"Error fetching user project count: {e}")

        # Tenant-wide active projects count
        return await Project.find({
            "tenant_id": tenant_id,
            "is_deleted": {"$ne": True},
            "status": {"$in": ACTIVE_PROJ_STATUSES}
        }).count()

    async def get_experiment_counts(
        self, *, tenant_id: UUID, user_id: Optional[UUID] = None
    ) -> Tuple[int, int, int]:
        """
        Count active vs completed vs review required experiments within user/tenant scope.
        Returns (active_count, completed_count, review_required_count).
        """
        if user_id:
            try:
                collab_exps = await ExperimentCollaborator.find({"user_id": user_id}).to_list()
                collab_exp_ids = [ce.experiment_id for ce in collab_exps if hasattr(ce, "experiment_id")]

                user_exp_filter = {
                    "tenant_id": tenant_id,
                    "is_deleted": {"$ne": True},
                    "$or": [
                        {"owner_id": user_id},
                        {"reviewer_id": user_id},
                        {"_id": {"$in": collab_exp_ids}}
                    ]
                }

                user_total = await Experiment.find(user_exp_filter).count()
                if user_total > 0:
                    active_count = await Experiment.find({
                        **user_exp_filter,
                        "status": {"$in": ACTIVE_EXP_STATUSES}
                    }).count()

                    completed_count = await Experiment.find({
                        **user_exp_filter,
                        "status": {"$in": COMPLETED_EXP_STATUSES}
                    }).count()

                    review_count = await Experiment.find({
                        **user_exp_filter,
                        "status": {"$in": REVIEW_EXP_STATUSES}
                    }).count()

                    return active_count, completed_count, review_count
            except Exception as e:
                logger.warning(f"Error fetching user experiment counts: {e}")

        # Fallback to tenant-wide counts
        active_count = await Experiment.find({
            "tenant_id": tenant_id,
            "is_deleted": {"$ne": True},
            "status": {"$in": ACTIVE_EXP_STATUSES}
        }).count()

        completed_count = await Experiment.find({
            "tenant_id": tenant_id,
            "is_deleted": {"$ne": True},
            "status": {"$in": COMPLETED_EXP_STATUSES}
        }).count()

        review_count = await Experiment.find({
            "tenant_id": tenant_id,
            "is_deleted": {"$ne": True},
            "status": {"$in": REVIEW_EXP_STATUSES}
        }).count()

        return active_count, completed_count, review_count

    async def get_recent_experiments(
        self, *, tenant_id: UUID, user_id: Optional[UUID] = None, limit: int = 5
    ) -> List[Experiment]:
        """Fetch top N recent experiments within user or tenant scope."""
        if user_id:
            try:
                collab_exps = await ExperimentCollaborator.find({"user_id": user_id}).to_list()
                collab_exp_ids = [ce.experiment_id for ce in collab_exps if hasattr(ce, "experiment_id")]

                user_exp_filter = {
                    "tenant_id": tenant_id,
                    "is_deleted": {"$ne": True},
                    "$or": [
                        {"owner_id": user_id},
                        {"reviewer_id": user_id},
                        {"_id": {"$in": collab_exp_ids}}
                    ]
                }
                user_exps = await Experiment.find(user_exp_filter).sort("-updated_at").limit(limit).to_list()
                if user_exps:
                    return user_exps
            except Exception as e:
                logger.warning(f"Error fetching recent user experiments: {e}")

        return await Experiment.find({
            "tenant_id": tenant_id,
            "is_deleted": {"$ne": True}
        }).sort("-updated_at").limit(limit).to_list()

    async def get_total_samples_count(self, *, tenant_id: UUID) -> int:
        """Count total registered samples for tenant."""
        try:
            return await Sample.find({"tenant_id": tenant_id, "is_deleted": {"$ne": True}}).count()
        except Exception as e:
            logger.warning(f"Error fetching samples count: {e}")
            return 0

    async def get_pending_notifications(
        self, *, tenant_id: UUID, user: User, limit: int = 5
    ) -> List[NotificationSummary]:
        """
        Generate unread notifications and contextual actionable alerts for the specified user.
        """
        notifications: List[NotificationSummary] = []
        try:
            # 1. Fetch persisted notifications from MongoDB collection
            from app.models.notification import Notification
            persisted = await Notification.find({
                "tenant_id": tenant_id,
                "user_id": user.id,
                "is_read": False,
            }).sort("-created_at").limit(limit).to_list()

            for n in persisted:
                notifications.append(
                    NotificationSummary(
                        id=n.id,
                        title=n.title,
                        message=n.message,
                        type=n.type or "info",
                        created_at=n.created_at or datetime.now(timezone.utc),
                        is_read=n.is_read,
                    )
                )

            # 2. If fewer than limit, check for user's experiments awaiting review
            if len(notifications) < limit:
                review_exps = await Experiment.find({
                    "tenant_id": tenant_id,
                    "is_deleted": {"$ne": True},
                    "status": {"$in": REVIEW_EXP_STATUSES},
                    "$or": [
                        {"reviewer_id": user.id},
                        {"owner_id": user.id}
                    ]
                }).limit(limit - len(notifications)).to_list()

                for exp in review_exps:
                    notifications.append(
                        NotificationSummary(
                            id=uuid4(),
                            title="Review Required",
                            message=f"Experiment '{exp.title}' ({exp.experiment_code}) is in review.",
                            type="action_required",
                            created_at=exp.updated_at or datetime.now(timezone.utc),
                            is_read=False,
                        )
                    )

            # 3. If still empty, check for user's active draft experiments
            if len(notifications) < limit:
                draft_exps = await Experiment.find({
                    "tenant_id": tenant_id,
                    "owner_id": user.id,
                    "is_deleted": {"$ne": True},
                    "status": {"$in": ["draft", "DRAFT", "Draft", ExperimentStatus.DRAFT]}
                }).limit(limit - len(notifications)).to_list()

                for exp in draft_exps:
                    notifications.append(
                        NotificationSummary(
                            id=uuid4(),
                            title="Draft Experiment",
                            message=f"Experiment '{exp.title}' is ready for protocol execution.",
                            type="info",
                            created_at=exp.updated_at or datetime.now(timezone.utc),
                            is_read=False,
                        )
                    )

            # 4. If completely empty, add a welcome guidance notification
            if not notifications:
                notifications.append(
                    NotificationSummary(
                        id=uuid4(),
                        title="Lab Workspace Ready",
                        message="Your ELN workspace is active. Create projects or experiments to begin research.",
                        type="info",
                        created_at=datetime.now(timezone.utc),
                        is_read=False,
                    )
                )

        except Exception as e:
            logger.warning(f"Error assembling notifications: {e}")

        return notifications[:limit]

    async def get_activity_feed(
        self, *, tenant_id: UUID, limit: int = 10
    ) -> List[ActivityFeedItem]:
        """Fetch recent platform activity feed from experiments, projects, and notes."""
        items: List[ActivityFeedItem] = []
        try:
            recent_exps = await Experiment.find({
                "tenant_id": tenant_id,
                "is_deleted": {"$ne": True}
            }).sort("-updated_at").limit(limit).to_list()

            for exp in recent_exps:
                status_str = str(exp.status.value) if hasattr(exp.status, "value") else str(exp.status)
                items.append(
                    ActivityFeedItem(
                        id=uuid4(),
                        operation="UPDATE" if exp.updated_at != exp.created_at else "CREATE",
                        entity_type="Experiment",
                        description=f"Experiment '{exp.title}' status is {status_str.replace('_', ' ').title()}",
                        performed_by_name="Research Team",
                        performed_at=exp.updated_at or exp.created_at or datetime.now(timezone.utc),
                    )
                )
        except Exception as e:
            logger.warning(f"Error assembling activity feed: {e}")

        return items[:limit]


dashboard_repo = DashboardRepository()
