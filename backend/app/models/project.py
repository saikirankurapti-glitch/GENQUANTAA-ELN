from typing import Optional, List
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4
from app.db.enums import ProjectStatus

class Project(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    owner_id: UUID
    name: str
    project_code: str = ""
    description: Optional[str] = None
    objective: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNED
    priority: str = "MEDIUM"
    tags: list[str] = Field(default_factory=list)
    visibility: str = "PRIVATE"
    metadata_json: dict = Field(default_factory=dict)
    is_archived: bool = False
    is_deleted: bool = False
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "projects"

class ProjectCollaborator(Document):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    user_id: UUID
    role: str = "collaborator"
    tenant_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "project_collaborators"

class ProjectAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    file_name: str
    file_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "project_attachments"
