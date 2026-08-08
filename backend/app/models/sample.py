from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4

class SampleType(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sample_types"

class SampleStorageLocation(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    freezer_unit: Optional[str] = None
    shelf: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sample_storage_locations"

class Sample(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    sample_type_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    name: str
    sample_code: str
    barcode: Optional[str] = None
    status: str = "available"
    quantity: float = 1.0
    unit: str = "mL"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "samples"

    @property
    def sample_name(self) -> str:
        return self.name

    @property
    def storage_location_id(self) -> Optional[UUID]:
        return self.location_id

class SampleChainOfCustody(Document):
    id: UUID = Field(default_factory=uuid4)
    sample_id: UUID
    user_id: UUID
    action: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sample_chain_of_custody"

class SampleAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    sample_id: UUID
    file_name: str
    file_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sample_attachments"

class SampleAliquot(Document):
    id: UUID = Field(default_factory=uuid4)
    parent_sample_id: UUID
    aliquot_code: str
    quantity: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sample_aliquots"
