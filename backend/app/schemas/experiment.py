from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.db.enums import ExperimentStatus


class ExperimentCollaboratorBase(BaseModel):
    user_id: UUID = Field(..., description="Target collaborator user identifier")
    role: str = Field("editor", description="Collaborator permission level: viewer, editor, lead, reviewer")


class ExperimentCollaboratorCreate(ExperimentCollaboratorBase):
    pass


class ExperimentCollaboratorRead(ExperimentCollaboratorBase):
    id: UUID = Field(..., description="Association identifier")
    added_at: datetime = Field(..., description="Timestamp when collaborator was added")
    added_by: Optional[UUID] = Field(None, description="User who granted access")

    model_config = ConfigDict(from_attributes=True)


class ExperimentAttachmentRead(BaseModel):
    id: UUID = Field(..., description="Attachment identifier")
    file_name: str = Field(..., description="Uploaded file name")
    file_path: str = Field(..., description="Secure storage path")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME classification")
    uploaded_by: Optional[UUID] = Field(None, description="Uploader user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class ExperimentBase(BaseModel):
    experiment_code: str = Field(..., min_length=2, max_length=64, description="Unique project-scoped experiment code (e.g. EXP-2026-001)")
    title: str = Field(..., min_length=2, max_length=255, description="Experiment title")
    objective: Optional[str] = Field(None, description="Objective description")
    hypothesis: Optional[str] = Field(None, description="Experimental hypothesis")
    description: Optional[str] = Field(None, description="Detailed procedures or description")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT, description="Current experiment status")
    priority: str = Field(default="MEDIUM", description="Priority level: LOW, MEDIUM, HIGH, CRITICAL")
    protocol_id: Optional[UUID] = Field(None, description="Associated protocol identifier")
    start_date: Optional[date] = Field(None, description="Actual or planned start date")
    planned_end_date: Optional[date] = Field(None, description="Planned end date")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")

    @field_validator("experiment_code")
    @classmethod
    def validate_experiment_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Experiment code cannot be blank.")
        return v

    @field_validator("start_date", "planned_end_date", mode="before")
    @classmethod
    def coerce_datetime_to_date(cls, v: Any) -> Any:
        """Strip time component from datetime values stored as date fields.

        PostgreSQL timestamps returned as datetime objects fail Pydantic v2's
        strict date validation. Extracting .date() makes validation succeed.
        """
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        return v



class ExperimentCreate(ExperimentBase):
    project_id: Optional[UUID] = Field(None, description="Parent Project identifier (optional - defaults to tenant workspace)")
    organization_id: Optional[UUID] = Field(None, description="Target Organization identifier")
    owner_id: Optional[UUID] = Field(None, description="Owner / Lead Scientist user identifier")
    reviewer_id: Optional[UUID] = Field(None, description="Designated Reviewer user identifier")


class ExperimentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    objective: Optional[str] = None
    hypothesis: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ExperimentStatus] = None
    priority: Optional[str] = None
    protocol_id: Optional[UUID] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    completed_date: Optional[date] = None
    reviewed_date: Optional[date] = None
    reviewer_id: Optional[UUID] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ExperimentArchiveRequest(BaseModel):
    archive_reason: Optional[str] = Field(None, description="Reason for archiving experiment")


class ExperimentRead(ExperimentBase):
    id: UUID = Field(..., description="Experiment unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: Optional[UUID] = Field(None, description="Organization identifier")
    project_id: Optional[UUID] = Field(None, description="Parent project identifier")
    owner_id: Optional[UUID] = Field(None, description="Owner user identifier")
    reviewer_id: Optional[UUID] = Field(None, description="Reviewer user identifier")
    completed_date: Optional[date] = Field(None, description="Completion date")
    reviewed_date: Optional[date] = Field(None, description="Review sign-off date")
    is_archived: bool = Field(False, description="Archive state flag")
    archived_at: Optional[datetime] = Field(None, description="Timestamp when archived")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ExperimentDetail(ExperimentRead):
    collaborators: List[ExperimentCollaboratorRead] = Field(default_factory=list, description="Assigned experiment collaborators")
    attachments: List[ExperimentAttachmentRead] = Field(default_factory=list, description="Attached data files and reports")


class ExperimentSummary(BaseModel):
    id: UUID
    experiment_code: str
    title: str
    status: ExperimentStatus
    priority: str
    is_archived: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentFilter(BaseModel):
    project_id: Optional[UUID] = None
    status: Optional[ExperimentStatus] = None
    priority: Optional[str] = None
    owner_id: Optional[UUID] = None
    is_archived: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search keyword matching code, title, or description")


class ExperimentPagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class ExperimentListResponse(BaseModel):
    items: List[ExperimentRead] = Field(default_factory=list, description="Page of experiment records")
    total: int = Field(0, description="Total matching experiment count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")


class CommentReplyRead(BaseModel):
    id: UUID
    author_id: UUID
    author_name: str
    author_role: str = "Researcher"
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentCommentCreate(BaseModel):
    section_id: str = Field(..., description="Referenced section or step ID (e.g. 'step_2', 'objective', 'results')")
    section_title: Optional[str] = Field(None, description="Human readable section label (e.g. 'Protocol Step 2')")
    target_text: Optional[str] = Field(None, description="Exact highlighted or referenced quote/line")
    comment: str = Field(..., min_length=1, description="Review feedback or question text")
    category: str = Field("QA_REVIEW", description="Category: QA_REVIEW, COMPLIANCE_CHECK, SCIENTIFIC_QUESTION, SUGGESTION")


class ExperimentCommentReplyCreate(BaseModel):
    comment: str = Field(..., min_length=1, description="Reply text")


class ExperimentCommentResolve(BaseModel):
    status: str = Field("resolved", description="Status: 'resolved' or 'open'")
    resolution_note: Optional[str] = Field(None, description="Optional note explaining resolution")


class ExperimentCommentRead(BaseModel):
    id: UUID
    experiment_id: UUID
    author_id: UUID
    author_name: str
    author_role: str
    section_id: str
    section_title: Optional[str] = None
    target_text: Optional[str] = None
    comment: str
    category: str = "QA_REVIEW"
    status: str = "open"  # 'open' | 'resolved'
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_at: datetime
    replies: List[CommentReplyRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
