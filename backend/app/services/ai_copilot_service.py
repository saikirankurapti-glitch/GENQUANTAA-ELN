import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_ai_copilot import ai_repo
from app.models.ai_copilot import AIConversation, AIJob, AIMessage
from app.models.identity import User
from app.schemas.ai_copilot import (
    ChatRequest,
    ChatResponse,
    CitationRead,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    PromptTemplateCreate,
    PromptTemplateRead,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)

logger = logging.getLogger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────

class ConversationNotFound(Exception):
    pass


class AIProviderError(Exception):
    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class JobNotFound(Exception):
    pass


# ── Provider abstraction ───────────────────────────────────────────────────────

class AIProviderBase(ABC):
    """Abstract base for AI provider implementations."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Return dict with keys: content, prompt_tokens, completion_tokens, total_tokens."""

    @abstractmethod
    async def embed_text(self, text: str, model: str) -> List[float]:
        """Return embedding vector as list of floats."""


class MockAIProvider(AIProviderBase):
    """
    Mock provider used when no real API key is configured.
    Returns deterministic placeholder responses for development/testing.
    """

    async def chat_completion(
        self, messages: List[Dict[str, str]], model: str, **kwargs: Any
    ) -> Dict[str, Any]:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        content = (
            f"[Mock AI Response] I received your message: '{last_user[:80]}'. "
            "In production this will be answered by the configured LLM provider."
        )
        return {
            "content": content,
            "prompt_tokens": len(last_user.split()),
            "completion_tokens": len(content.split()),
            "total_tokens": len(last_user.split()) + len(content.split()),
        }

    async def embed_text(self, text: str, model: str) -> List[float]:
        # Deterministic mock: hash-based unit vector with 1536 dimensions
        import hashlib
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        vec = [(((h >> i) & 0xF) - 7.5) / 7.5 for i in range(1536)]
        magnitude = sum(v ** 2 for v in vec) ** 0.5 or 1.0
        return [v / magnitude for v in vec]


def get_provider(provider_name: str) -> AIProviderBase:
    """Factory returning the appropriate provider implementation."""
    # In production, swap MockAIProvider with OpenAIProvider, AzureOpenAIProvider, etc.
    # based on provider_name and env config.
    return MockAIProvider()


# ── System prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPTS: Dict[str, str] = {
    "qa": (
        "You are a scientific research assistant embedded in a laboratory ELN system. "
        "Answer questions accurately, cite your sources, and flag uncertainty explicitly. "
        "Context from the lab knowledge base will be provided where relevant."
    ),
    "summarize": (
        "You are a scientific writing assistant. Produce concise, structured summaries "
        "of laboratory experiments and notebook entries. Use Markdown with clear headings."
    ),
    "draft_protocol": (
        "You are a senior lab scientist. Draft clear, numbered SOPs with safety notes, "
        "reagent lists, equipment requirements, and step-by-step procedures."
    ),
    "sample_insights": (
        "You are a laboratory data analyst. Interpret sample metadata, quality metrics, "
        "and storage conditions to provide actionable insights."
    ),
    "sequence_interpret": (
        "You are a molecular biologist. Interpret DNA, RNA, and Protein sequences, "
        "predict function, identify conserved domains, and suggest annotation."
    ),
    "citation": (
        "You are a scientific literature specialist. Generate accurate citations "
        "in APA format for the provided source documents."
    ),
}


# ── Service ────────────────────────────────────────────────────────────────────

class AIService:
    """Service layer orchestrating RAG pipeline, provider calls, and audit logging."""

    async def chat(
        self,
        db: AsyncSession,
        *,
        req: ChatRequest,
        tenant_id: UUID,
        organization_id: UUID,
        current_user: User,
    ) -> ChatResponse:
        """
        Core chat endpoint: retrieves or creates a conversation, runs optional RAG
        retrieval, calls the AI provider, persists messages, and writes audit log.
        """
        provider_name = req.provider or "openai"
        model_name = req.model_name or "gpt-4o"
        provider = get_provider(provider_name)

        # 1. Resolve or create conversation
        if req.conversation_id:
            conv = await ai_repo.get_conversation(
                db, conversation_id=req.conversation_id, tenant_id=tenant_id
            )
            if not conv:
                raise ConversationNotFound(f"Conversation {req.conversation_id} not found.")
        else:
            conv = await ai_repo.create_conversation(
                db,
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=current_user.id,
                context_type=req.context_type,
                context_id=req.context_id,
                provider=provider_name,
                model_name=model_name,
            )

        # 2. RAG retrieval
        citations: List[CitationRead] = []
        rag_context = ""
        if req.use_rag:
            try:
                query_vec = await provider.embed_text(req.message, model="text-embedding-3-small")
                docs_scores = await ai_repo.semantic_search(
                    db, tenant_id=tenant_id, query_vector=query_vec,
                    top_k=5, source_type=req.context_type
                )
                if docs_scores:
                    rag_lines = []
                    for doc, score in docs_scores:
                        excerpt = doc.content[:500]
                        rag_lines.append(f"[Source: {doc.title}]\n{excerpt}")
                        citations.append(CitationRead(
                            document_id=doc.id,
                            title=doc.title,
                            source_type=doc.source_type,
                            relevance_score=round(score, 4),
                            excerpt=excerpt,
                        ))
                    rag_context = "\n\n---\n\n".join(rag_lines)
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        # 3. Build message history
        system_prompt = SYSTEM_PROMPTS.get(req.feature, SYSTEM_PROMPTS["qa"])
        if rag_context:
            system_prompt += f"\n\n## Retrieved Context\n\n{rag_context}"

        history_msgs = [{"role": "system", "content": system_prompt}]
        if conv.messages:
            for m in conv.messages[-10:]:  # Last 10 turns for context window
                history_msgs.append({"role": m.role, "content": m.content})
        history_msgs.append({"role": "user", "content": req.message})

        # 4. Call provider
        t0 = time.monotonic()
        status = "success"
        error_msg = None
        ai_result: Dict[str, Any] = {}

        try:
            ai_result = await provider.chat_completion(history_msgs, model=model_name)
        except Exception as e:
            status = "error"
            error_msg = str(e)
            ai_result = {
                "content": f"AI provider error: {e}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            logger.error(f"AIService: provider error [{provider_name}]: {e}")

        latency_ms = int((time.monotonic() - t0) * 1000)

        # 5. Persist user + assistant messages
        citation_meta = {"citations": [c.model_dump(mode="json") for c in citations]}
        await ai_repo.add_message(db, conversation_id=conv.id, role="user", content=req.message)
        assistant_msg = await ai_repo.add_message(
            db,
            conversation_id=conv.id,
            role="assistant",
            content=ai_result.get("content", ""),
            prompt_tokens=ai_result.get("prompt_tokens", 0),
            completion_tokens=ai_result.get("completion_tokens", 0),
            total_tokens=ai_result.get("total_tokens", 0),
            latency_ms=latency_ms,
            citation_metadata=citation_meta,
        )

        # 6. Write audit log
        await ai_repo.write_audit_log(
            db,
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=current_user.id,
            conversation_id=conv.id,
            provider=provider_name,
            model_name=model_name,
            feature=req.feature,
            prompt_tokens=ai_result.get("prompt_tokens", 0),
            completion_tokens=ai_result.get("completion_tokens", 0),
            total_tokens=ai_result.get("total_tokens", 0),
            latency_ms=latency_ms,
            status=status,
            error_message=error_msg,
            citation_count=len(citations),
        )

        return ChatResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            content=ai_result.get("content", ""),
            citations=citations,
            prompt_tokens=ai_result.get("prompt_tokens", 0),
            completion_tokens=ai_result.get("completion_tokens", 0),
            total_tokens=ai_result.get("total_tokens", 0),
            latency_ms=latency_ms,
            provider=provider_name,
            model_name=model_name,
        )

    async def list_conversations(
        self, db: AsyncSession, *, tenant_id: UUID, current_user: User
    ) -> List[AIConversation]:
        return await ai_repo.list_conversations(db, tenant_id=tenant_id, user_id=current_user.id)

    async def get_conversation(
        self, db: AsyncSession, *, conversation_id: UUID, tenant_id: UUID
    ) -> AIConversation:
        conv = await ai_repo.get_conversation(
            db, conversation_id=conversation_id, tenant_id=tenant_id
        )
        if not conv:
            raise ConversationNotFound(f"Conversation {conversation_id} not found.")
        return conv

    async def create_prompt_template(
        self, db: AsyncSession, *, obj_in: PromptTemplateCreate, tenant_id: UUID, current_user: User
    ):
        return await ai_repo.create_prompt_template(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )

    async def list_prompt_templates(
        self, db: AsyncSession, *, tenant_id: UUID, category: Optional[str] = None
    ):
        return await ai_repo.list_prompt_templates(db, tenant_id=tenant_id, category=category)

    async def add_knowledge_document(
        self,
        db: AsyncSession,
        *,
        obj_in: KnowledgeDocumentCreate,
        tenant_id: UUID,
        organization_id: UUID,
        current_user: User,
    ):
        return await ai_repo.create_knowledge_document(
            db, obj_in=obj_in, tenant_id=tenant_id, organization_id=organization_id
        )

    async def generate_and_store_embedding(
        self,
        db: AsyncSession,
        *,
        document_id: UUID,
        content: str,
        tenant_id: UUID,
        provider_name: str = "openai",
    ):
        provider = get_provider(provider_name)
        vector = await provider.embed_text(content, model="text-embedding-3-small")
        return await ai_repo.store_embedding(
            db,
            document_id=document_id,
            tenant_id=tenant_id,
            embedding_model="text-embedding-3-small",
            vector=vector,
        )

    async def semantic_search(
        self,
        db: AsyncSession,
        *,
        req: SemanticSearchRequest,
        tenant_id: UUID,
        provider_name: str = "openai",
    ) -> SemanticSearchResponse:
        provider = get_provider(provider_name)
        query_vec = await provider.embed_text(req.query, model="text-embedding-3-small")
        docs_scores = await ai_repo.semantic_search(
            db,
            tenant_id=tenant_id,
            query_vector=query_vec,
            top_k=req.top_k,
            source_type=req.source_type,
            min_score=req.min_score,
        )
        results = [
            SemanticSearchResult(
                document_id=doc.id,
                title=doc.title,
                source_type=doc.source_type,
                excerpt=doc.content[:400],
                relevance_score=round(score, 4),
            )
            for doc, score in docs_scores
        ]
        return SemanticSearchResponse(query=req.query, results=results, total=len(results))

    async def get_job(
        self, db: AsyncSession, *, job_id: UUID, tenant_id: UUID
    ) -> AIJob:
        job = await ai_repo.get_job(db, job_id=job_id, tenant_id=tenant_id)
        if not job:
            raise JobNotFound(f"AI job {job_id} not found.")
        return job


ai_service = AIService()
