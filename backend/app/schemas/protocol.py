from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProtocolStepBase(BaseModel):
    step_number: int = Field(..., ge=1, description="Sequential step index (1, 2, 3...)")
    title: str = Field(..., min_length=2, max_length=255, description="Step headline title")
    instructions: str = Field(..., min_length=2, description="Detailed action instructions")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Estimated duration in minutes")
    safety_notes: Optional[str] = Field(None, description="Personal Protective Equipment (PPE) & hazard safety notes")


class ProtocolStepCreate(ProtocolStepBase):
    pass


class ProtocolStepRead(ProtocolStepBase):
    id: UUID = Field(..., description="Step unique identifier")
    protocol_id: UUID = Field(..., description="Parent protocol identifier")

    model_config = ConfigDict(from_attributes=True)


class ProtocolApprovalBase(BaseModel):
    status: str = Field(..., description="Approval decision: approved or rejected")
    comments: Optional[str] = Field(None, description="Reviewer feedback comments")


class ProtocolApprovalCreate(ProtocolApprovalBase):
    pass


class ProtocolApprovalRead(ProtocolApprovalBase):
    id: UUID = Field(..., description="Approval record identifier")
    protocol_id: UUID = Field(..., description="Associated protocol identifier")
    approver_id: UUID = Field(..., description="Approver user identifier")
    decision_date: datetime = Field(..., description="Decision timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProtocolAttachmentRead(BaseModel):
    id: UUID = Field(..., description="Attachment identifier")
    filename: str = Field(..., description="Uploaded SOP document name")
    blob_path: str = Field(..., description="Blob storage path")
    mime_type: Optional[str] = Field(None, description="MIME classification")
    file_size: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 checksum")
    uploaded_by: Optional[UUID] = Field(None, description="Uploader user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProtocolVersionRead(BaseModel):
    id: UUID = Field(..., description="Version snapshot identifier")
    protocol_id: UUID = Field(..., description="Parent protocol identifier")
    version_number: int = Field(..., description="Version number")
    content_snapshot: Dict[str, Any] = Field(..., description="Immutable version snapshot")
    change_reason: Optional[str] = Field(None, description="Change reason")
    created_by: Optional[UUID] = Field(None, description="Author user identifier")
    created_at: datetime = Field(..., description="Version creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProtocolBase(BaseModel):
    protocol_code: str = Field(..., min_length=2, max_length=64, description="Tenant-scoped unique protocol code (e.g. PRT-SOP-001)")
    title: str = Field(..., min_length=2, max_length=255, description="Protocol title")
    description: Optional[str] = Field(None, description="Detailed protocol summary")
    category: str = Field("general", description="Category: molecular_biology, biochemistry, analytical, cell_culture, general")
    status: str = Field("draft", description="Status: draft, in_review, approved, rejected, archived")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")

    @field_validator("protocol_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Protocol code cannot be blank.")
        return v


class ProtocolCreate(ProtocolBase):
    organization_id: UUID = Field(..., description="Target Organization identifier")
    reviewer_id: Optional[UUID] = Field(None, description="Assigned reviewer user identifier")
    steps: List[ProtocolStepCreate] = Field(default_factory=list, description="Initial protocol steps sequence")


class ProtocolUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    reviewer_id: Optional[UUID] = None
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: Optional[str] = Field(None, description="Audit change reason for incrementing version snapshot")


class ProtocolRead(ProtocolBase):
    id: UUID = Field(..., description="Protocol unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: UUID = Field(..., description="Organization identifier")
    current_version: int = Field(1, description="Current version number")
    owner_id: Optional[UUID] = Field(None, description="Owner user identifier")
    reviewer_id: Optional[UUID] = Field(None, description="Reviewer user identifier")
    approval_date: Optional[datetime] = Field(None, description="Approval date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProtocolDetail(ProtocolRead):
    steps: List[ProtocolStepRead] = Field(default_factory=list, description="Sequential steps")
    versions: List[ProtocolVersionRead] = Field(default_factory=list, description="Version snapshots")
    attachments: List[ProtocolAttachmentRead] = Field(default_factory=list, description="Attached documents")
    approvals: List[ProtocolApprovalRead] = Field(default_factory=list, description="Approval history")


class ProtocolSummary(BaseModel):
    id: UUID
    protocol_code: str
    title: str
    category: str
    status: str
    current_version: int

    model_config = ConfigDict(from_attributes=True)


class ProtocolFilter(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[UUID] = None
    search: Optional[str] = Field(None, description="Search keyword matching protocol_code, title, or description")


class ProtocolPagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class ProtocolListResponse(BaseModel):
    items: List[ProtocolRead] = Field(default_factory=list, description="Page of protocol records")
    total: int = Field(0, description="Total matching protocol count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")
