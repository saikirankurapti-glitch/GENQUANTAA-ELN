from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ExperimentSummary(BaseModel):
    id: UUID = Field(..., description="Unique experiment identifier")
    title: str = Field(..., description="Title of the experiment")
    experiment_number: str = Field(..., description="Unique experiment code or number")
    status: str = Field(..., description="Current experiment status")
    updated_at: datetime = Field(..., description="Timestamp of last update")

    model_config = ConfigDict(from_attributes=True)


class NotificationSummary(BaseModel):
    id: UUID = Field(..., description="Notification identifier")
    title: str = Field(..., description="Alert headline")
    message: str = Field(..., description="Detailed message body")
    type: str = Field(..., description="Alert severity or classification (info, warning, action_required)")
    created_at: datetime = Field(..., description="Timestamp when notification was issued")
    is_read: bool = Field(False, description="Read state toggle")

    model_config = ConfigDict(from_attributes=True)


class QuickAction(BaseModel):
    id: str = Field(..., description="Action unique identifier key")
    label: str = Field(..., description="Human-readable button label")
    action_type: str = Field(..., description="Type of action (create_project, create_experiment, etc.)")
    target_url: str = Field(..., description="Frontend navigation route target")
    icon: str = Field(..., description="UI icon descriptor name")
    required_permission: Optional[str] = Field(None, description="RBAC permission required to trigger action")


class ActivityFeedItem(BaseModel):
    id: UUID = Field(..., description="Audit log entry identifier")
    operation: str = Field(..., description="Action performed (CREATE, UPDATE, DELETE, SIGN)")
    entity_type: str = Field(..., description="Target domain entity (Project, Experiment, Sample, etc.)")
    description: str = Field(..., description="Human-readable audit action summary")
    performed_by_name: Optional[str] = Field(None, description="Name of user who performed action")
    performed_at: datetime = Field(..., description="Timestamp of event occurrence")

    model_config = ConfigDict(from_attributes=True)


class AICopilotShortcut(BaseModel):
    shortcut_id: str = Field(..., description="Unique copilot shortcut identifier")
    title: str = Field(..., description="Shortcut title description")
    suggested_prompt: str = Field(..., description="Pre-filled prompt string for AI Assistant")
    category: str = Field(..., description="Copilot functional category (research, compliance, protocol, analytics)")


class DashboardResponse(BaseModel):
    project_count: int = Field(0, description="Total active projects/workspaces for current user/tenant")
    active_experiment_count: int = Field(0, description="Active/in-progress experiments count")
    completed_experiment_count: int = Field(0, description="Completed/approved experiments count")
    review_required_count: int = Field(0, description="Experiments requiring review")
    total_samples_count: int = Field(0, description="Total registered samples in inventory")
    recent_experiments: List[ExperimentSummary] = Field(default_factory=list, description="Top N recently accessed experiments")
    pending_notifications: List[NotificationSummary] = Field(default_factory=list, description="Unread pending notifications")
    quick_actions: List[QuickAction] = Field(default_factory=list, description="Contextual quick create actions")
    activity_feed: List[ActivityFeedItem] = Field(default_factory=list, description="Recent tenant activity audit feed")
    ai_copilot_shortcuts: List[AICopilotShortcut] = Field(default_factory=list, description="AI Copilot prompt shortcuts")
