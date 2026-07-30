from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.db.enums import ProjectStatus


class ProjectCollaboratorBase(BaseModel):
    user_id: UUID = Field(..., description="Target collaborator user identifier")
    role: str = Field("viewer", description="Collaborator permission level: viewer, editor, lead, admin")


class ProjectCollaboratorCreate(ProjectCollaboratorBase):
    pass


class ProjectCollaboratorRead(ProjectCollaboratorBase):
    id: UUID = Field(..., description="Association identifier")
    added_at: datetime = Field(..., description="Timestamp when collaborator was added")
    added_by: Optional[UUID] = Field(None, description="User who granted collaborator access")

    model_config = ConfigDict(from_attributes=True)


class ProjectAttachmentRead(BaseModel):
    id: UUID = Field(..., description="Attachment identifier")
    file_name: str = Field(..., description="Uploaded file name")
    file_path: str = Field(..., description="Secure storage file path")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type classification")
    uploaded_by: Optional[UUID] = Field(None, description="Uploader user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProjectBase(BaseModel):
    project_code: str = Field(..., min_length=2, max_length=64, description="Unique tenant-scoped project code (e.g. PRJ-2026-001)")
    name: str = Field(..., min_length=2, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Detailed project description")
    objective: Optional[str] = Field(None, description="Research objective statement")
    status: ProjectStatus = Field(default=ProjectStatus.PLANNED, description="Current project status")
    priority: str = Field(default="MEDIUM", description="Project priority: LOW, MEDIUM, HIGH, CRITICAL")
    tags: List[str] = Field(default_factory=list, description="Tag labels for categorization")
    visibility: str = Field(default="PRIVATE", description="Visibility level: PRIVATE, ORGANIZATION, PUBLIC")
    start_date: Optional[date] = Field(None, description="Planned or actual project start date")
    target_end_date: Optional[date] = Field(None, description="Target completion date")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom JSON metadata attributes")

    @field_validator("project_code")
    @classmethod
    def validate_project_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Project code cannot be blank.")
        return v


class ProjectCreate(ProjectBase):
    organization_id: UUID = Field(..., description="Target Organization identifier")
    owner_id: Optional[UUID] = Field(None, description="Primary Principal Investigator / Owner user identifier")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    completed_date: Optional[date] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ProjectArchiveRequest(BaseModel):
    archive_reason: Optional[str] = Field(None, description="Reason for archiving the project")


class ProjectRead(ProjectBase):
    id: UUID = Field(..., description="Project unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: UUID = Field(..., description="Organization identifier")
    owner_id: Optional[UUID] = Field(None, description="Owner user identifier")
    completed_date: Optional[date] = Field(None, description="Actual project completion date")
    is_archived: bool = Field(False, description="Archive flag")
    archived_at: Optional[datetime] = Field(None, description="Timestamp when archived")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectRead):
    collaborators: List[ProjectCollaboratorRead] = Field(default_factory=list, description="Assigned project collaborators")
    attachments: List[ProjectAttachmentRead] = Field(default_factory=list, description="Attached project documents")
    experiment_count: int = Field(0, description="Total experiments linked to project")


class ProjectSummary(BaseModel):
    id: UUID
    project_code: str
    name: str
    status: ProjectStatus
    priority: str
    is_archived: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectFilter(BaseModel):
    status: Optional[ProjectStatus] = None
    priority: Optional[str] = None
    owner_id: Optional[UUID] = None
    is_archived: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search keyword matching code, name, or description")


class ProjectPagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class ProjectListResponse(BaseModel):
    items: List[ProjectRead] = Field(default_factory=list, description="Page of project records")
    total: int = Field(0, description="Total matching project count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")
