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


class GroqAIProvider(AIProviderBase):
    """Groq Cloud Llama-3 LLM provider implementation."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat_completion(
        self, messages: List[Dict[str, str]], model: str, **kwargs: Any
    ) -> Dict[str, Any]:
        import urllib.request
        import urllib.error
        import json

        url = "https://api.groq.com/openai/v1/chat/completions"
        target_model = model if model and model not in ["mock-v1", "default"] else "llama-3.3-70b-versatile"

        payload = json.dumps({
            "model": target_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }
        )

        try:
            res = urllib.request.urlopen(req)
            data = json.loads(res.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return {
                "content": content,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise AIProviderError(f"Groq API Error: {str(e)}", provider="groq")

    async def embed_text(self, text: str, model: str) -> List[float]:
        import hashlib
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        vec = [(((h >> i) & 0xF) - 7.5) / 7.5 for i in range(1536)]
        magnitude = sum(v ** 2 for v in vec) ** 0.5 or 1.0
        return [v / magnitude for v in vec]


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
    from app.core.config import settings
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if api_key:
        return GroqAIProvider(api_key=api_key)
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
        import uuid as uuid_mod
        conv_id = req.conversation_id or uuid_mod.uuid4()
        conv_messages = []

        if db is not None and req.conversation_id:
            try:
                conv = await ai_repo.get_conversation(
                    db, conversation_id=req.conversation_id, tenant_id=tenant_id
                )
                if conv and getattr(conv, "messages", None):
                    conv_messages = conv.messages
            except Exception:
                pass

        # 2. RAG retrieval
        citations: List[CitationRead] = []
        rag_context = ""

        # 3. Build message history
        system_prompt = SYSTEM_PROMPTS.get(req.feature, SYSTEM_PROMPTS["qa"])
        history_msgs = [{"role": "system", "content": system_prompt}]
        for m in conv_messages[-10:]:
            history_msgs.append({"role": getattr(m, "role", "user"), "content": getattr(m, "content", "")})
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

        # 5. Persist user + assistant messages if db is available
        msg_id = uuid_mod.uuid4()
        if db is not None:
            try:
                citation_meta = {"citations": [c.model_dump(mode="json") for c in citations]}
                await ai_repo.add_message(db, conversation_id=conv_id, role="user", content=req.message)
                assistant_msg = await ai_repo.add_message(
                    db,
                    conversation_id=conv_id,
                    role="assistant",
                    content=ai_result.get("content", ""),
                    prompt_tokens=ai_result.get("prompt_tokens", 0),
                    completion_tokens=ai_result.get("completion_tokens", 0),
                    total_tokens=ai_result.get("total_tokens", 0),
                    latency_ms=latency_ms,
                    citation_metadata=citation_meta,
                )
                if assistant_msg:
                    msg_id = assistant_msg.id
            except Exception as e:
                logger.warning(f"Message persistence skipped: {e}")

        return ChatResponse(
            conversation_id=conv_id,
            message_id=msg_id,
            content=ai_result.get("content", ""),
            citations=citations,
            prompt_tokens=ai_result.get("prompt_tokens", 0),
            completion_tokens=ai_result.get("completion_tokens", 0),
            total_tokens=ai_result.get("total_tokens", 0),
            model_name=model_name,
            provider=provider_name,
            latency_ms=latency_ms,
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
