import logging
from typing import List, Set, Optional, Any
from uuid import UUID

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

logger = logging.getLogger(__name__)


class DashboardService:
    """Service orchestrating aggregated dashboard data assembly."""

    def build_quick_actions(self, permissions: Set[str]) -> List[QuickAction]:
        """Build contextual quick create actions based on granted user permissions."""
        actions: List[QuickAction] = [
            QuickAction(
                id="qa_new_experiment",
                label="New Experiment",
                action_type="create_experiment",
                target_url="/notebook",
                icon="flask",
                required_permission="experiment.create",
            ),
            QuickAction(
                id="qa_new_project",
                label="New Project",
                action_type="create_project",
                target_url="/projects",
                icon="folder-plus",
                required_permission="project.create",
            ),
            QuickAction(
                id="qa_register_sample",
                label="Register Sample",
                action_type="register_sample",
                target_url="/samples",
                icon="vial",
                required_permission="sample.create",
            ),
            QuickAction(
                id="qa_ai_copilot",
                label="AI Copilot",
                action_type="launch_copilot",
                target_url="/ai-copilot",
                icon="sparkles",
                required_permission=None,
            ),
        ]
        return actions

    def build_ai_copilot_shortcuts(self) -> List[AICopilotShortcut]:
        """Build AI Copilot shortcut prompts for lab productivity."""
        return [
            AICopilotShortcut(
                shortcut_id="copilot_summary",
                title="Summarize Active Experiments",
                suggested_prompt="Provide a concise summary of my active experiments, current status, and next steps.",
                category="research",
            ),
            AICopilotShortcut(
                shortcut_id="copilot_protocol_draft",
                title="Generate Protocol Template",
                suggested_prompt="Draft a standard operating procedure (SOP) for CRISPR transfection and western blot validation.",
                category="protocol",
            ),
            AICopilotShortcut(
                shortcut_id="copilot_compliance_check",
                title="Check 21 CFR Part 11 Compliance",
                suggested_prompt="Verify that all experiment entries have valid electronic sign-offs and complete audit trails.",
                category="compliance",
            ),
            AICopilotShortcut(
                shortcut_id="copilot_inventory_alert",
                title="Sample Storage & Inventory",
                suggested_prompt="List all biological samples currently stored in cryo racks with temperature monitoring status.",
                category="analytics",
            ),
        ]

    async def get_dashboard(
        self, db: Optional[Any] = None, *, user: User, tenant_id: UUID
    ) -> DashboardResponse:
        """
        Assemble aggregated Dashboard response for current user.
        """
        if isinstance(tenant_id, str):
            tenant_id = UUID(tenant_id)

        # 1. Project & Workspace Counts (Scoped to user with fallback to tenant)
        project_count = await dashboard_repo.get_project_count(
            tenant_id=tenant_id, user_id=user.id
        )

        # 2. Experiment Counts (Active, Completed, Review Required)
        active_exp_count, completed_exp_count, review_required_count = await dashboard_repo.get_experiment_counts(
            tenant_id=tenant_id, user_id=user.id
        )

        # 3. Total Samples
        total_samples_count = await dashboard_repo.get_total_samples_count(
            tenant_id=tenant_id
        )

        # 4. Recent Experiments (Scoped to user)
        recent_exps_db = await dashboard_repo.get_recent_experiments(
            tenant_id=tenant_id, user_id=user.id, limit=6
        )

        recent_experiments: List[ExperimentSummary] = []
        for exp in recent_exps_db:
            status_val = str(exp.status.value) if hasattr(exp.status, "value") else str(exp.status)
            recent_experiments.append(
                ExperimentSummary(
                    id=exp.id,
                    title=exp.title or "Untitled Experiment",
                    experiment_number=exp.experiment_code or f"EXP-{str(exp.id)[:6].upper()}",
                    status=status_val,
                    updated_at=exp.updated_at or exp.created_at,
                )
            )

        # 5. Pending Notifications & Action Items
        pending_notifications = await dashboard_repo.get_pending_notifications(
            tenant_id=tenant_id, user=user, limit=5
        )

        # 6. Activity Feed
        activity_feed = await dashboard_repo.get_activity_feed(
            tenant_id=tenant_id, limit=10
        )

        # 7. Quick Actions & Copilot Shortcuts
        quick_actions = self.build_quick_actions(set())
        ai_copilot_shortcuts = self.build_ai_copilot_shortcuts()

        logger.info(
            f"DashboardService: Assembled dashboard for user {user.username} ({user.id}) | "
            f"Projects: {project_count}, Active Exps: {active_exp_count}, "
            f"Completed Exps: {completed_exp_count}, Reviews: {review_required_count}"
        )

        return DashboardResponse(
            project_count=project_count,
            active_experiment_count=active_exp_count,
            completed_experiment_count=completed_exp_count,
            review_required_count=review_required_count,
            total_samples_count=total_samples_count,
            recent_experiments=recent_experiments,
            pending_notifications=pending_notifications,
            quick_actions=quick_actions,
            activity_feed=activity_feed,
            ai_copilot_shortcuts=ai_copilot_shortcuts,
        )


dashboard_service = DashboardService()
