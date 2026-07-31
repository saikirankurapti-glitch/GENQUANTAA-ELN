from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Citation ──────────────────────────────────────────────────────────────────

class CitationRead(BaseModel):
    document_id: UUID = Field(..., description="Knowledge document ID used as citation source")
    title: str = Field(..., description="Document title")
    source_type: str = Field(..., description="Source type: experiment, notebook, protocol, etc.")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
    excerpt: Optional[str] = Field(None, description="Relevant excerpt from source document")

    model_config = ConfigDict(from_attributes=True)


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    citation_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Conversations ─────────────────────────────────────────────────────────────

class ConversationRead(BaseModel):
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    title: str
    context_type: Optional[str] = None
    context_id: Optional[UUID] = None
    provider: str
    model_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's prompt message")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation to continue")
    context_type: Optional[str] = Field(
        None, description="Domain context type: experiment, notebook, protocol, sample, sequence"
    )
    context_id: Optional[UUID] = Field(None, description="ID of the context entity")
    feature: str = Field(
        "qa", description="AI feature: qa, summarize, draft_protocol, sample_insights, sequence_interpret, citation"
    )
    use_rag: bool = Field(True, description="Whether to augment with RAG retrieval")
    provider: Optional[str] = Field(None, description="Provider override: openai, azure, compatible")
    model_name: Optional[str] = Field(None, description="Model override: gpt-4o, gpt-4-turbo, etc.")

    @field_validator("feature")
    @classmethod
    def validate_feature(cls, v: str) -> str:
        allowed = {
            "qa",
            "summarize",
            "draft_protocol",
            "sample_insights",
            "sequence_interpret",
            "citation",
            # AI Fill All section-specific features
            "fill_objective",
            "fill_materials",
            "fill_results",
            "summarize_experiment",
        }
        if v not in allowed:
            raise ValueError(f"feature must be one of: {', '.join(sorted(allowed))}")
        return v


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    role: str = "assistant"
    content: str
    citations: List[CitationRead] = Field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    provider: str
    model_name: str


# ── Prompt Templates ──────────────────────────────────────────────────────────

class PromptTemplateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    category: str = Field(..., min_length=2, max_length=64,
                          description="Category: summarize, draft_protocol, qa, insights")
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    user_prompt_template: str = Field(..., min_length=5)
    variables: Dict[str, Any] = Field(default_factory=dict)


class PromptTemplateRead(PromptTemplateCreate):
    id: UUID
    tenant_id: UUID
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Knowledge Documents ───────────────────────────────────────────────────────

class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    source_type: str = Field(..., description="Source type: experiment, notebook, protocol, manual, paper")
    source_id: Optional[UUID] = None
    content: str = Field(..., min_length=10)
    chunk_index: int = Field(0, ge=0)
    total_chunks: int = Field(1, ge=1)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentRead(KnowledgeDocumentCreate):
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    content_hash: str
    is_indexed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Semantic Search ───────────────────────────────────────────────────────────

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language search query")
    top_k: int = Field(5, ge=1, le=20, description="Number of top results to return")
    source_type: Optional[str] = Field(None, description="Filter by source type")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum cosine similarity threshold")


class SemanticSearchResult(BaseModel):
    document_id: UUID
    title: str
    source_type: str
    excerpt: str
    relevance_score: float


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult] = Field(default_factory=list)
    total: int = 0


# ── AI Jobs ───────────────────────────────────────────────────────────────────

class AIJobRead(BaseModel):
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    job_type: str
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AIAuditRead(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    conversation_id: Optional[UUID] = None
    provider: str
    model_name: str
    feature: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    status: str
    error_message: Optional[str] = None
    citation_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
