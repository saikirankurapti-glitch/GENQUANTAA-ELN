from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field


class Notification(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    user_id: UUID  # Recipient user identifier
    title: str
    message: str
    type: str = Field(default="assignment", description="assignment, review, status_change, mention, info, alert")
    entity_type: Optional[str] = Field(default="project", description="project, experiment, protocol, sample, notebook")
    entity_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None
    sender_name: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"
        indexes = [
            "tenant_id",
            "user_id",
            "is_read",
            "-created_at",
        ]
