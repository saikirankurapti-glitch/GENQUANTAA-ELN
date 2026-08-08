from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4

class Sequence(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    experiment_id: Optional[UUID] = None
    sample_id: Optional[UUID] = None
    name: str
    sequence_type: str = "DNA"
    sequence_data: str
    length: int = 0
    status: str = "active"
    gc_content: float = 0.0
    molecular_weight: float = 0.0
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sequences"

    @property
    def sequence_name(self) -> str:
        return self.name

    @property
    def sequence_code(self) -> str:
        return f"SEQ-{str(self.id).split('-')[0].upper()}"

    @property
    def source(self) -> str:
        return "Unknown"

    @property
    def version(self) -> int:
        return 1

    @property
    def organization_id(self) -> UUID:
        return self.tenant_id

class SequenceVersion(Document):
    id: UUID = Field(default_factory=uuid4)
    sequence_id: UUID
    version: int
    sequence_data: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sequence_versions"

class SequenceAnnotation(Document):
    id: UUID = Field(default_factory=uuid4)
    sequence_id: UUID
    label: str
    start_pos: int
    end_pos: int

    class Settings:
        name = "sequence_annotations"

class SequenceAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    sequence_id: UUID
    file_name: str
    file_path: str

    class Settings:
        name = "sequence_attachments"

class SequenceAnalysisResult(Document):
    id: UUID = Field(default_factory=uuid4)
    sequence_id: UUID
    analysis_type: str
    result_data: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "sequence_analysis_results"
