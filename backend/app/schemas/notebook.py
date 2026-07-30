from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotebookTagBase(BaseModel):
    tag_name: str = Field(..., min_length=1, max_length=64, description="Tag label")
    color: str = Field("#3B82F6", description="HEX color string")


class NotebookTagCreate(NotebookTagBase):
    pass


class NotebookTagRead(NotebookTagBase):
    id: UUID = Field(..., description="Tag identifier")

    model_config = ConfigDict(from_attributes=True)


class NotebookCommentBase(BaseModel):
    comment: str = Field(..., min_length=1, description="Comment text body")
    parent_comment_id: Optional[UUID] = Field(None, description="Parent comment for nested replies")


class NotebookCommentCreate(NotebookCommentBase):
    pass


class NotebookCommentRead(NotebookCommentBase):
    id: UUID = Field(..., description="Comment identifier")
    author_id: UUID = Field(..., description="Author user identifier")
    created_at: datetime = Field(..., description="Comment creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class NotebookAttachmentRead(BaseModel):
    id: UUID = Field(..., description="Attachment identifier")
    filename: str = Field(..., description="File name")
    blob_path: str = Field(..., description="Storage blob path")
    mime_type: Optional[str] = Field(None, description="MIME classification")
    file_size: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 file checksum")
    uploaded_by: Optional[UUID] = Field(None, description="Uploader user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class NotebookEntryVersionRead(BaseModel):
    id: UUID = Field(..., description="Version record identifier")
    notebook_entry_id: UUID = Field(..., description="Parent notebook entry identifier")
    version_number: int = Field(..., description="Incremental version index")
    content_snapshot: Dict[str, Any] = Field(..., description="Immutable document content snapshot")
    change_reason: Optional[str] = Field(None, description="Reason for version edit")
    created_by: Optional[UUID] = Field(None, description="Author user identifier")
    created_at: datetime = Field(..., description="Version creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class NotebookEntryBase(BaseModel):
    entry_number: str = Field(..., min_length=2, max_length=64, description="Unique experiment-scoped entry number (e.g. NBE-001)")
    title: str = Field(..., min_length=2, max_length=255, description="Entry headline title")
    content: Dict[str, Any] = Field(default_factory=dict, description="Rich text or structured document JSON content")
    entry_type: str = Field("observation", description="Classification (observation, procedure, result, analysis)")

    @field_validator("entry_number")
    @classmethod
    def validate_entry_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Entry number cannot be blank.")
        return v


class NotebookEntryCreate(NotebookEntryBase):
    experiment_id: UUID = Field(..., description="Parent Experiment identifier")
    organization_id: UUID = Field(..., description="Target Organization identifier")


class NotebookEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    content: Optional[Dict[str, Any]] = None
    entry_type: Optional[str] = None
    change_reason: Optional[str] = Field(None, description="Mandatory audit change reason for incrementing version snapshot")


class NotebookEntryRead(NotebookEntryBase):
    id: UUID = Field(..., description="Notebook entry unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: UUID = Field(..., description="Organization identifier")
    experiment_id: UUID = Field(..., description="Parent experiment identifier")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary snippet")
    summary_status: str = Field("pending", description="AI summary status: pending, generating, completed, failed")
    current_version: int = Field(1, description="Latest version number")
    is_locked: bool = Field(False, description="Lock state flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class NotebookEntryDetail(NotebookEntryRead):
    versions: List[NotebookEntryVersionRead] = Field(default_factory=list, description="Historical version snapshots")
    attachments: List[NotebookAttachmentRead] = Field(default_factory=list, description="Attached files")
    comments: List[NotebookCommentRead] = Field(default_factory=list, description="Comments")
    tags: List[NotebookTagRead] = Field(default_factory=list, description="Tags")


class NotebookEntrySummary(BaseModel):
    id: UUID
    entry_number: str
    title: str
    current_version: int
    summary_status: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotebookFilter(BaseModel):
    experiment_id: Optional[UUID] = None
    entry_type: Optional[str] = None
    search: Optional[str] = Field(None, description="Search term matching title or content")


class NotebookPagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class NotebookListResponse(BaseModel):
    items: List[NotebookEntryRead] = Field(default_factory=list, description="Page of notebook records")
    total: int = Field(0, description="Total matching entry count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")
