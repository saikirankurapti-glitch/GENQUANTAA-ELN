from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SampleTypeRead(BaseModel):
    id: UUID = Field(..., description="Sample type identifier")
    name: str = Field(..., description="Sample type name")
    code: str = Field(..., description="Sample type classification code")
    description: Optional[str] = Field(None, description="Description")

    model_config = ConfigDict(from_attributes=True)


class StorageLocationRead(BaseModel):
    id: UUID = Field(..., description="Storage location identifier")
    name: str = Field(..., description="Storage location name (e.g. Freezer #3 - Rack B)")
    building: Optional[str] = None
    room: Optional[str] = None
    freezer_unit: Optional[str] = None
    shelf_box: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChainOfCustodyRead(BaseModel):
    id: UUID = Field(..., description="Audit record identifier")
    sample_id: UUID = Field(..., description="Associated sample identifier")
    action: str = Field(..., description="Action performed (registered, check_out, check_in, transferred)")
    custodian_id: UUID = Field(..., description="Custodian user identifier")
    performed_at: datetime = Field(..., description="Event timestamp")
    remarks: Optional[str] = Field(None, description="Custodian remarks")

    model_config = ConfigDict(from_attributes=True)


class SampleAttachmentRead(BaseModel):
    id: UUID = Field(..., description="Attachment identifier")
    filename: str = Field(..., description="Uploaded file name")
    blob_path: str = Field(..., description="Blob storage path")
    mime_type: Optional[str] = Field(None, description="MIME classification")
    file_size: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 checksum")
    uploaded_by: Optional[UUID] = Field(None, description="Uploader user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class SampleBase(BaseModel):
    sample_code: str = Field(..., min_length=2, max_length=64, description="Experiment-scoped sample code (e.g. SMP-001)")
    barcode: str = Field(..., min_length=2, max_length=128, description="Globally unique tenant barcode string (e.g. BC-100234)")
    sample_name: str = Field(..., min_length=2, max_length=255, description="Human-readable specimen name")
    quantity: float = Field(default=0.0, ge=0.0, description="Specimen quantity")
    unit: str = Field(default="mL", description="Quantity unit (mL, uL, mg, ug, vials)")
    concentration: Optional[str] = Field(None, description="Concentration rating (e.g. 10 mM, 5 mg/mL)")
    storage_temperature: str = Field(default="-80C", description="Required storage temperature rating")
    collection_date: Optional[date] = Field(None, description="Specimen collection date")
    expiry_date: Optional[date] = Field(None, description="Specimen expiration date")
    status: str = Field(default="available", description="Sample status: available, consumed, destroyed, expired")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom JSON metadata attributes")

    @field_validator("sample_code", "barcode")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Code/barcode cannot be blank.")
        return v


class SampleCreate(SampleBase):
    experiment_id: UUID = Field(..., description="Parent Experiment identifier")
    organization_id: UUID = Field(..., description="Target Organization identifier")
    sample_type_id: Optional[UUID] = Field(None, description="Sample type classification identifier")
    storage_location_id: Optional[UUID] = Field(None, description="Storage location identifier")
    parent_sample_id: Optional[UUID] = Field(None, description="Parent specimen identifier for aliquots/derivatives")


class SampleUpdate(BaseModel):
    sample_name: Optional[str] = Field(None, min_length=2, max_length=255)
    quantity: Optional[float] = Field(None, ge=0.0)
    unit: Optional[str] = None
    concentration: Optional[str] = None
    storage_temperature: Optional[str] = None
    storage_location_id: Optional[UUID] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class SampleRead(SampleBase):
    id: UUID = Field(..., description="Sample unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: Optional[UUID] = Field(None, description="Organization identifier")
    experiment_id: UUID = Field(..., description="Parent experiment identifier")
    sample_type_id: Optional[UUID] = Field(None, description="Sample type identifier")
    storage_location_id: Optional[UUID] = Field(None, description="Storage location identifier")
    parent_sample_id: Optional[UUID] = Field(None, description="Parent sample identifier")
    is_archived: bool = Field(False, description="Archive flag")
    archived_at: Optional[datetime] = Field(None, description="Archival timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class SampleDetail(SampleRead):
    chain_of_custody: List[ChainOfCustodyRead] = Field(default_factory=list, description="Audit chain of custody events")
    attachments: List[SampleAttachmentRead] = Field(default_factory=list, description="Attached reports and CoAs")
    storage_location: Optional[StorageLocationRead] = Field(None, description="Detailed storage location")
    sample_type: Optional[SampleTypeRead] = Field(None, description="Sample type information")


class SampleSummary(BaseModel):
    id: UUID
    sample_code: str
    barcode: str
    sample_name: str
    status: str
    quantity: float
    unit: str

    model_config = ConfigDict(from_attributes=True)


class SampleFilter(BaseModel):
    experiment_id: Optional[UUID] = None
    sample_type_id: Optional[UUID] = None
    storage_location_id: Optional[UUID] = None
    status: Optional[str] = None
    barcode: Optional[str] = None
    search: Optional[str] = Field(None, description="Search term matching sample_code, barcode, or sample_name")


class SamplePagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class SampleListResponse(BaseModel):
    items: List[SampleRead] = Field(default_factory=list, description="Page of sample records")
    total: int = Field(0, description="Total matching sample count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")
