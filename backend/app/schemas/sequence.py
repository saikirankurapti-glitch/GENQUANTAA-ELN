from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ── Valid alphabets ────────────────────────────────────────────────────────────
VALID_DNA_CHARS = set("ACGT")
VALID_RNA_CHARS = set("ACGU")
VALID_AA_CHARS = set("ACDEFGHIKLMNPQRSTVWY")


def _validate_sequence_alphabet(seq_type: str, sequence_data: str) -> str:
    """Validate and clean sequence_data for its type without throwing errors."""
    from app.utils.bioinformatics import clean_sequence
    return clean_sequence(sequence_data)


def _compute_gc_content(seq_type: str, sequence_data: str) -> Optional[float]:
    """Compute GC content (%) for DNA and RNA. Returns None for Protein."""
    if seq_type.upper() not in ("DNA", "RNA"):
        return None
    upper = sequence_data.upper()
    if not upper:
        return 0.0
    gc = upper.count("G") + upper.count("C")
    return round((gc / len(upper)) * 100, 4)


# ── Sub-entity schemas ─────────────────────────────────────────────────────────

class SequenceVersionRead(BaseModel):
    id: UUID
    sequence_id: UUID
    version_number: int
    sequence_data: str
    length: int
    gc_content: Optional[float] = None
    change_summary: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SequenceAnnotationCreate(BaseModel):
    annotation_type: str = Field(..., min_length=1, max_length=64,
                                 description="Type: ORF, promoter, CDS, binding_site, repeat")
    label: str = Field(..., min_length=1, max_length=128, description="Human-readable label")
    start_position: int = Field(..., ge=1, description="1-based start residue position")
    end_position: int = Field(..., ge=2, description="1-based end residue position (exclusive)")
    strand: Optional[str] = Field(None, pattern=r'^[+-]$', description="Strand: + or -")
    notes: Optional[str] = Field(None, description="Additional notes")

    @model_validator(mode="after")
    def validate_positions(self) -> "SequenceAnnotationCreate":
        if self.end_position <= self.start_position:
            raise ValueError("end_position must be greater than start_position.")
        return self


class SequenceAnnotationRead(SequenceAnnotationCreate):
    id: UUID
    sequence_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SequenceAttachmentRead(BaseModel):
    id: UUID
    sequence_id: UUID
    filename: str
    blob_path: str
    mime_type: Optional[str] = None
    file_size: int
    checksum: str
    uploaded_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SequenceAnalysisResultRead(BaseModel):
    id: UUID
    sequence_id: UUID
    analysis_type: str
    tool_name: Optional[str] = None
    tool_version: Optional[str] = None
    result_summary: Optional[str] = None
    result_json: Dict[str, Any] = Field(default_factory=dict)
    performed_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Core Sequence schemas ──────────────────────────────────────────────────────

class SequenceBase(BaseModel):
    sequence_code: str = Field(..., min_length=2, max_length=64,
                               description="Tenant-scoped unique code (e.g. SEQ-DNA-001)")
    sequence_name: str = Field(..., min_length=2, max_length=255, description="Sequence display name")
    sequence_type: str = Field(..., description="Type: DNA, RNA, or Protein")
    source: Optional[str] = Field(None, max_length=128, description="Source organism or vector")
    molecular_weight: Optional[float] = Field(None, ge=0, description="Molecular weight in Daltons")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("sequence_code")
    @classmethod
    def upper_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("sequence_code cannot be blank.")
        return v

    @field_validator("sequence_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in ("DNA", "RNA", "PROTEIN"):
            raise ValueError("sequence_type must be DNA, RNA, or Protein.")
        return v


class SequenceCreate(SequenceBase):
    organization_id: UUID = Field(..., description="Organization identifier")
    experiment_id: Optional[UUID] = Field(None, description="Linked Experiment identifier")
    sample_id: Optional[UUID] = Field(None, description="Linked Sample identifier")
    sequence_data: str = Field(..., min_length=1, description="Raw sequence string")

    @model_validator(mode="after")
    def validate_and_normalise(self) -> "SequenceCreate":
        self.sequence_data = _validate_sequence_alphabet(self.sequence_type, self.sequence_data)
        return self


class SequenceUpdate(BaseModel):
    sequence_name: Optional[str] = Field(None, min_length=2, max_length=255)
    sequence_data: Optional[str] = Field(None, min_length=1)
    sequence_type: Optional[str] = None
    source: Optional[str] = None
    molecular_weight: Optional[float] = Field(None, ge=0)
    metadata_json: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = Field(None, max_length=512,
                                          description="Brief description of changes for version history")


class SequenceRead(SequenceBase):
    id: UUID
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    sample_id: Optional[UUID] = None
    sequence_data: str
    length: int
    gc_content: Optional[float] = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SequenceDetail(SequenceRead):
    seq_versions: List[SequenceVersionRead] = Field(default_factory=list)
    annotations: List[SequenceAnnotationRead] = Field(default_factory=list)
    attachments: List[SequenceAttachmentRead] = Field(default_factory=list)
    analysis_results: List[SequenceAnalysisResultRead] = Field(default_factory=list)


class SequenceSummary(BaseModel):
    id: UUID
    sequence_code: str
    sequence_name: str
    sequence_type: str
    length: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class SequenceFilter(BaseModel):
    sequence_type: Optional[str] = None
    status: Optional[str] = None
    experiment_id: Optional[UUID] = None
    sample_id: Optional[UUID] = None
    search: Optional[str] = Field(None, description="Search keyword (code or name)")


class SequencePagination(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at")
    sort_order: str = Field("desc")


class SequenceListResponse(BaseModel):
    items: List[SequenceRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


# ── FASTA upload ───────────────────────────────────────────────────────────────

class FastaRecord(BaseModel):
    """A single parsed FASTA record."""
    header: str
    sequence_data: str


class FastaUploadResponse(BaseModel):
    registered: int = Field(..., description="Number of sequences successfully registered")
    failed: int = Field(0, description="Number of records that failed validation")
    errors: List[str] = Field(default_factory=list)
