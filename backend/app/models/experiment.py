from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4
from app.db.enums import ExperimentStatus

class Experiment(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    project_id: UUID
    owner_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    protocol_id: Optional[UUID] = None
    experiment_code: str
    title: str
    objective: Optional[str] = None
    hypothesis: Optional[str] = None
    description: Optional[str] = None
    status: ExperimentStatus = ExperimentStatus.DRAFT
    priority: str = "MEDIUM"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    is_archived: bool = False
    is_deleted: bool = False
    start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    reviewed_date: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "experiments"

class ExperimentCollaborator(Document):
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    user_id: UUID
    role: str = "collaborator"
    tenant_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "experiment_collaborators"

class ExperimentAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    file_name: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    uploaded_by: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "experiment_attachments"


class ExperimentQAComment(Document):
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    tenant_id: UUID
    author_id: UUID
    author_name: str
    author_role: str = "QA"
    section_id: str
    section_title: Optional[str] = None
    target_text: Optional[str] = None
    comment: str
    category: str = "QA_REVIEW"
    status: str = "open"  # 'open' | 'resolved'
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    replies: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "experiment_qa_comments"
