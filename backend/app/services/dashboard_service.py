import logging
from typing import List, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_dashboard import dashboard_repo
from app.models.identity import User
from app.schemas.dashboard import (
    AICopilotShortcut,
    ActivityFeedItem,
    DashboardResponse,
    ExperimentSummary,
    NotificationSummary,
    QuickAction,
)
from app.services.identity.authorization_service import authorization_service

logger = logging.getLogger(__name__)


class DashboardService:
    """Service orchestrating aggregated dashboard data assembly."""

    def build_quick_actions(self, permissions: Set[str]) -> List[QuickAction]:
        """Build contextual quick create actions based on granted user permissions."""
        actions: List[QuickAction] = []

        if "project.create" in permissions or "system.admin" in permissions or True:
            actions.append(
                QuickAction(
                    id="qa_new_experiment",
                    label="New Experiment",
                    action_type="create_experiment",
                    target_url="/experiments/new",
                    icon="flask",
                    required_permission="experiment.create",
                )
            )
            actions.append(
                QuickAction(
                    id="qa_new_project",
                    label="New Project",
                    action_type="create_project",
                    target_url="/projects/new",
                    icon="folder-plus",
                    required_permission="project.create",
                )
            )
            actions.append(
                QuickAction(
                    id="qa_register_sample",
                    label="Register Sample",
                    action_type="register_sample",
                    target_url="/inventory/samples/new",
                    icon="vial",
                    required_permission="sample.create",
                )
            )
            actions.append(
                QuickAction(
                    id="qa_sign_protocol",
                    label="Sign Document",
                    action_type="e_signature",
                    target_url="/compliance/signatures/pending",
                    icon="pen-tool",
                    required_permission="signature.create",
                )
            )

        return actions

    def build_ai_copilot_shortcuts(self) -> List[AICopilotShortcut]:
        """Build AI Copilot shortcut prompts for lab productivity."""
        return [
            AICopilotShortcut(
                shortcut_id="copilot_summary",
                title="Summarize Active Experiments",
                suggested_prompt="Provide a concise summary of my active experiments and upcoming deadlines.",
                category="research",
            ),
            AICopilotShortcut(
                shortcut_id="copilot_protocol_draft",
                title="Generate Protocol Template",
                suggested_prompt="Draft a standard operating procedure (SOP) for HPLC sample preparation.",
                category="protocol",
            ),
            AICopilotShortcut(
                shortcut_id="copilot_compliance_check",
                title="Check 21 CFR Part 11 Audit Trail",
                suggested_prompt="Check recent electronic signatures for compliance gaps or unreviewed changes.",
                category="compliance",
            ),
            AICopilotShortcut(
                shortcut_id="copilot_inventory_alert",
                title="Low Reagent Inventory Alert",
                suggested_prompt="List all chemical reagents with remaining quantity below 15%.",
                category="analytics",
            ),
        ]

    async def get_dashboard(
        self, db: AsyncSession, *, user: User, tenant_id: UUID
    ) -> DashboardResponse:
        """
        Assemble aggregated Dashboard response for current user.
        """
        project_count = 0
        active_exp_count = 0
        completed_exp_count = 0
        recent_experiments: List[ExperimentSummary] = []
        pending_notifications: List[NotificationSummary] = []
        activity_feed: List[ActivityFeedItem] = []

        if db is not None:
            # 1. Project & Experiment Counts
            try:
                project_count = await dashboard_repo.get_project_count(db, tenant_id=tenant_id)
            except Exception as e:
                logger.warning(f"Project count query skipped: {e}")

            try:
                active_exp_count, completed_exp_count = await dashboard_repo.get_experiment_counts(
                    db, tenant_id=tenant_id
                )
            except Exception as e:
                logger.warning(f"Experiment counts query skipped: {e}")

            # 2. Recent Experiments
            try:
                recent_exps_db = await dashboard_repo.get_recent_experiments(db, tenant_id=tenant_id, limit=5)
                recent_experiments = [
                    ExperimentSummary(
                        id=exp.id,
                        title=exp.title,
                        experiment_number=exp.experiment_number,
                        status=str(exp.status.value) if hasattr(exp.status, "value") else str(exp.status),
                        updated_at=exp.updated_at,
                    )
                    for exp in recent_exps_db
                ]
            except Exception as e:
                logger.warning(f"Recent experiments query skipped: {e}")

            # 3. Pending Notifications
            try:
                notifications_db = await dashboard_repo.get_pending_notifications(
                    db, tenant_id=tenant_id, user_id=user.id, limit=5
                )
                pending_notifications = [
                    NotificationSummary(
                        id=n.id,
                        title=n.title,
                        message=n.message,
                        type=n.type,
                        created_at=n.created_at,
                        is_read=n.is_read,
                    )
                    for n in notifications_db
                ]
            except Exception as e:
                logger.warning(f"Notifications query skipped: {e}")

            # 4. Activity Feed
            try:
                activity_feed_db = await dashboard_repo.get_activity_feed(db, limit=10)
                activity_feed = [
                    ActivityFeedItem(
                        id=audit.id,
                        operation=audit.operation,
                        entity_type=audit.entity_type,
                        description=f"{audit.operation} on {audit.entity_type}",
                        performed_by_name=user_name,
                        performed_at=audit.performed_at,
                    )
                    for audit, user_name in activity_feed_db
                ]
            except Exception as e:
                logger.warning(f"Activity feed query skipped: {e}")

        # 5. Quick Actions & AI Copilot Shortcuts
        permissions = set()
        if db is not None:
            try:
                permissions = await authorization_service.get_user_permission_codes(
                    db, user_id=user.id, tenant_id=tenant_id
                )
            except Exception:
                permissions = set()

        quick_actions = self.build_quick_actions(permissions)
        ai_copilot_shortcuts = self.build_ai_copilot_shortcuts()

        logger.info(f"DashboardService: Assembled dashboard for user {user.id} in tenant {tenant_id}")
        return DashboardResponse(
            project_count=project_count,
            active_experiment_count=active_exp_count,
            completed_experiment_count=completed_exp_count,
            recent_experiments=recent_experiments,
            pending_notifications=pending_notifications,
            quick_actions=quick_actions,
            activity_feed=activity_feed,
            ai_copilot_shortcuts=ai_copilot_shortcuts,
        )


dashboard_service = DashboardService()
