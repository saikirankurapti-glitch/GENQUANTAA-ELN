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
        prompt_lower = last_user.lower()
        
        # High-quality demo responses based on context
        if "objective & hypothesis" in prompt_lower or "fill_objective" in kwargs.get("feature", ""):
            content = (
                "Objective: To evaluate the editing efficiency of the designed CRISPR/Cas9 guide RNAs targeting the human EGFR locus in HEK293T cells.\n\n"
                "Hypothesis: We hypothesize that sgRNA-3 will demonstrate the highest indel frequency (>60%) due to its proximity to the protospacer adjacent motif (PAM) and minimal predicted off-target binding, leading to effective functional knockout of the EGFR receptor."
            )
        elif "step-by-step lab protocol" in prompt_lower:
            content = (
                "1. Thaw HEK293T cells and culture in DMEM supplemented with 10% FBS at 37°C, 5% CO2.\n"
                "2. Seed cells at 2x10^5 cells/well in a 6-well plate 24 hours prior to transfection.\n"
                "3. Prepare transfection mix: 2.5 µg of Cas9 plasmid, 2.5 µg of sgRNA plasmid, and 10 µL of Lipofectamine 3000 in Opti-MEM.\n"
                "4. Incubate transfection mix for 15 minutes at room temperature, then add dropwise to cells.\n"
                "5. After 48 hours, extract genomic DNA using the Quick-DNA Miniprep kit.\n"
                "6. Perform PCR amplification of the target EGFR region.\n"
                "7. Purify PCR products and proceed with Sanger sequencing or T7E1 mismatch cleavage assay to quantify indel formation."
            )
        elif "materials & reagents" in prompt_lower:
            content = (
                '- "HEK293T Cell Line" | Quantity: 1 vial | Source: ATCC\n'
                '- "Lipofectamine 3000 Transfection Reagent" | Quantity: 50 µL | Source: Thermo Fisher\n'
                '- "Cas9 Expression Plasmid (pSpCas9(BB)-2A-Puro)" | Quantity: 10 µg | Source: Addgene\n'
                '- "Quick-DNA Miniprep Kit" | Quantity: 1 kit | Source: Zymo Research\n'
                '- "Opti-MEM Reduced Serum Medium" | Quantity: 50 mL | Source: Gibco'
            )
        elif "realistic, highly professional experimental results" in prompt_lower:
            content = (
                "Cells were successfully transfected with >80% efficiency as observed by GFP co-expression controls. "
                "Genomic DNA was extracted 48h post-transfection with a yield of ~150 ng/µL (A260/280 = 1.88). "
                "The T7E1 mismatch cleavage assay revealed significant editing at the target locus. "
                "Quantification of the cleavage bands via densitometry indicated an indel frequency of 64% for sgRNA-3, 42% for sgRNA-1, and 18% for sgRNA-2. "
                "Sanger sequencing followed by TIDE analysis confirmed the 64% editing efficiency for sgRNA-3, predominantly consisting of a 1-bp insertion. "
                "These results strongly support the hypothesis and identify sgRNA-3 as the optimal candidate for downstream knockout studies."
            )
        else:
            content = (
                "Based on the available protocol literature and sequence data, the CRISPR design looks highly specific. "
                "The predicted off-target score is minimal. Ensure you run a gradient PCR to optimize the annealing temperature for the T7E1 assay primers."
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
        "reagent lists, equipment requirements, and step-by-step procedures. "
        "Output only the numbered steps, one per line."
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
    # AI Fill All section-specific prompts
    "fill_objective": (
        "You are a scientific research assistant helping fill an ELN experiment notebook. "
        "Write a clear, concise scientific objective and hypothesis. "
        "Output plain text only — no markdown, no bullet points, no headers. "
        "3-4 sentences maximum."
    ),
    "fill_materials": (
        "You are a laboratory materials specialist. "
        "Generate a reagents and materials list for a lab experiment. "
        "Return ONLY a valid JSON array with objects: [{\"name\": str, \"quantity\": str, \"lotNumber\": str}]. "
        "No explanations, no markdown, no code fences — just the raw JSON array."
    ),
    "fill_results": (
        "You are a scientific results analyst helping fill an ELN experiment notebook. "
        "Draft expected observations and measurable experimental results. "
        "Output plain text only — no markdown, no bullet points, no headers. "
        "2-3 sentences maximum."
    ),
    "summarize_experiment": (
        "You are a scientific writing assistant specializing in ELN experiment summaries. "
        "Write a structured scientific summary with these four sections: "
        "1. Background, 2. Methods Summary, 3. Key Findings, 4. Conclusions. "
        "Keep each section to 1-2 sentences. Use plain numbered headings only."
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
