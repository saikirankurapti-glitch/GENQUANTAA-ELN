from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user, get_current_tenant
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.ai_copilot import (
    AIJobRead,
    ChatRequest,
    ChatResponse,
    ConversationRead,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    PromptTemplateCreate,
    PromptTemplateRead,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.ai_copilot_service import (
    AIProviderError,
    ConversationNotFound,
    JobNotFound,
    ai_service,
)

router = APIRouter()


@router.get(
    "/conversations",
    response_model=List[ConversationRead],
    status_code=status.HTTP_200_OK,
    summary="List AI Conversations",
    description="Fetch all AI Copilot conversations for the current user.",
)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    convs = await ai_service.list_conversations(
        db, tenant_id=current_tenant.id, current_user=current_user
    )
    return [ConversationRead.model_validate(c) for c in convs]


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Chat",
    description=(
        "Send a message to the AI Copilot. Supports multi-turn conversations, "
        "RAG retrieval, and feature-specific prompting (summarize, draft_protocol, qa, etc.)."
    ),
)
async def chat(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    req: ChatRequest,
) -> Any:
    try:
        return await ai_service.chat(
            db,
            req=req,
            tenant_id=current_tenant.id,
            organization_id=current_user.organization_id
            if hasattr(current_user, "organization_id")
            else current_tenant.id,
            current_user=current_user,
        )
    except ConversationNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": str(e), "provider": e.provider},
        )


@router.get(
    "/conversations/{id}",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation",
    description="Fetch a conversation with full message history.",
)
async def get_conversation(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        conv = await ai_service.get_conversation(
            db, conversation_id=id, tenant_id=current_tenant.id
        )
        return ConversationRead.model_validate(conv)
    except ConversationNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/prompts",
    response_model=PromptTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Prompt Template",
    description="Register a reusable AI prompt template scoped to the current tenant.",
)
async def create_prompt_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    obj_in: PromptTemplateCreate,
) -> Any:
    template = await ai_service.create_prompt_template(
        db, obj_in=obj_in, tenant_id=current_tenant.id, current_user=current_user
    )
    return PromptTemplateRead.model_validate(template)


@router.get(
    "/prompts",
    response_model=List[PromptTemplateRead],
    status_code=status.HTTP_200_OK,
    summary="List Prompt Templates",
    description="List active prompt templates for the current tenant.",
)
async def list_prompt_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    category: Optional[str] = Query(None, description="Filter by category"),
) -> Any:
    templates = await ai_service.list_prompt_templates(
        db, tenant_id=current_tenant.id, category=category
    )
    return [PromptTemplateRead.model_validate(t) for t in templates]


@router.post(
    "/documents",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Knowledge Document",
    description="Index a document chunk into the tenant RAG knowledge base.",
)
async def add_knowledge_document(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    obj_in: KnowledgeDocumentCreate,
) -> Any:
    doc = await ai_service.add_knowledge_document(
        db,
        obj_in=obj_in,
        tenant_id=current_tenant.id,
        organization_id=current_tenant.id,
        current_user=current_user,
    )
    return KnowledgeDocumentRead.model_validate(doc)


@router.post(
    "/embeddings",
    status_code=status.HTTP_200_OK,
    summary="Generate Embedding",
    description="Generate and store a vector embedding for an indexed knowledge document.",
)
async def generate_embedding(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    document_id: UUID = Query(..., description="Knowledge document ID to embed"),
    content: str = Query(..., min_length=1, description="Text content to embed"),
) -> Any:
    emb = await ai_service.generate_and_store_embedding(
        db,
        document_id=document_id,
        content=content,
        tenant_id=current_tenant.id,
    )
    return {"embedding_id": str(emb.id), "dimensions": emb.embedding_dimensions}


@router.get(
    "/search",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Search",
    description="Search the tenant knowledge base using natural language with pgvector similarity.",
)
async def semantic_search(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=3, description="Natural language search query"),
    top_k: int = Query(5, ge=1, le=20),
    source_type: Optional[str] = Query(None),
    min_score: float = Query(0.5, ge=0.0, le=1.0),
) -> Any:
    req = SemanticSearchRequest(
        query=q, top_k=top_k, source_type=source_type, min_score=min_score
    )
    return await ai_service.semantic_search(db, req=req, tenant_id=current_tenant.id)


@router.get(
    "/jobs/{id}",
    response_model=AIJobRead,
    status_code=status.HTTP_200_OK,
    summary="Get AI Job",
    description="Fetch the status of a background AI job (indexing, bulk embedding).",
)
async def get_job(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        job = await ai_service.get_job(db, job_id=id, tenant_id=current_tenant.id)
        return AIJobRead.model_validate(job)
    except JobNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
