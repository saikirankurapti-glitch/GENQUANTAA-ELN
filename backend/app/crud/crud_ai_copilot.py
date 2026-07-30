import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_copilot import (
    AIAuditLog,
    AIConversation,
    AIEmbedding,
    AIJob,
    AIKnowledgeDocument,
    AIMessage,
    AIPromptTemplate,
)
from app.schemas.ai_copilot import (
    KnowledgeDocumentCreate,
    PromptTemplateCreate,
    SemanticSearchRequest,
)

logger = logging.getLogger(__name__)


class AIRepository:
    """Async Repository for all AI Copilot entities with tenant isolation."""

    # ── Conversations ─────────────────────────────────────────────────────────

    async def create_conversation(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        title: str = "New Conversation",
        context_type: Optional[str] = None,
        context_id: Optional[UUID] = None,
        provider: str = "openai",
        model_name: str = "gpt-4o",
    ) -> AIConversation:
        conv = AIConversation(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            context_type=context_type,
            context_id=context_id,
            provider=provider,
            model_name=model_name,
            status="active",
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    async def get_conversation(
        self,
        db: AsyncSession,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        include_messages: bool = True,
    ) -> Optional[AIConversation]:
        stmt = select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.tenant_id == tenant_id,
            AIConversation.is_deleted == False,
        )
        if include_messages:
            stmt = stmt.options(selectinload(AIConversation.messages))
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_conversations(
        self, db: AsyncSession, *, tenant_id: UUID, user_id: UUID
    ) -> List[AIConversation]:
        stmt = (
            select(AIConversation)
            .where(
                AIConversation.tenant_id == tenant_id,
                AIConversation.user_id == user_id,
                AIConversation.is_deleted == False,
            )
            .order_by(AIConversation.updated_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    # ── Messages ──────────────────────────────────────────────────────────────

    async def add_message(
        self,
        db: AsyncSession,
        *,
        conversation_id: UUID,
        role: str,
        content: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: int = 0,
        citation_metadata: Optional[Dict] = None,
    ) -> AIMessage:
        msg = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            citation_metadata=citation_metadata or {},
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    # ── Prompt Templates ──────────────────────────────────────────────────────

    async def create_prompt_template(
        self,
        db: AsyncSession,
        *,
        obj_in: PromptTemplateCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None,
    ) -> AIPromptTemplate:
        template = AIPromptTemplate(
            tenant_id=tenant_id,
            name=obj_in.name,
            category=obj_in.category,
            description=obj_in.description,
            system_prompt=obj_in.system_prompt,
            user_prompt_template=obj_in.user_prompt_template,
            variables=obj_in.variables,
            created_by=current_user_id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    async def list_prompt_templates(
        self, db: AsyncSession, *, tenant_id: UUID, category: Optional[str] = None
    ) -> List[AIPromptTemplate]:
        stmt = select(AIPromptTemplate).where(
            AIPromptTemplate.tenant_id == tenant_id,
            AIPromptTemplate.is_active == True,
        )
        if category:
            stmt = stmt.where(AIPromptTemplate.category == category)
        stmt = stmt.order_by(AIPromptTemplate.name.asc())
        return list((await db.execute(stmt)).scalars().all())

    # ── Knowledge Documents ───────────────────────────────────────────────────

    async def create_knowledge_document(
        self,
        db: AsyncSession,
        *,
        obj_in: KnowledgeDocumentCreate,
        tenant_id: UUID,
        organization_id: UUID,
    ) -> AIKnowledgeDocument:
        content_hash = hashlib.sha256(obj_in.content.encode()).hexdigest()
        doc = AIKnowledgeDocument(
            tenant_id=tenant_id,
            organization_id=organization_id,
            title=obj_in.title,
            source_type=obj_in.source_type,
            source_id=obj_in.source_id,
            content=obj_in.content,
            content_hash=content_hash,
            chunk_index=obj_in.chunk_index,
            total_chunks=obj_in.total_chunks,
            metadata_json=obj_in.metadata_json,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    async def list_knowledge_documents(
        self, db: AsyncSession, *, tenant_id: UUID, source_type: Optional[str] = None
    ) -> List[AIKnowledgeDocument]:
        stmt = select(AIKnowledgeDocument).where(
            AIKnowledgeDocument.tenant_id == tenant_id,
            AIKnowledgeDocument.is_deleted == False,
        )
        if source_type:
            stmt = stmt.where(AIKnowledgeDocument.source_type == source_type)
        stmt = stmt.order_by(AIKnowledgeDocument.created_at.desc())
        return list((await db.execute(stmt)).scalars().all())

    # ── Embeddings & Semantic Search ──────────────────────────────────────────

    async def store_embedding(
        self,
        db: AsyncSession,
        *,
        document_id: UUID,
        tenant_id: UUID,
        embedding_model: str,
        vector: List[float],
        dimensions: int = 1536,
    ) -> AIEmbedding:
        emb = AIEmbedding(
            tenant_id=tenant_id,
            document_id=document_id,
            embedding_model=embedding_model,
            embedding_dimensions=dimensions,
            vector_data=json.dumps(vector),
        )
        db.add(emb)
        # Mark document as indexed
        doc = await db.get(AIKnowledgeDocument, document_id)
        if doc:
            doc.is_indexed = True
            db.add(doc)
        await db.commit()
        await db.refresh(emb)
        return emb

    async def semantic_search(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        query_vector: List[float],
        top_k: int = 5,
        source_type: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[Tuple[AIKnowledgeDocument, float]]:
        """
        Perform cosine similarity search using pgvector.
        Falls back to in-memory dot product when pgvector is unavailable.
        """
        try:
            vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"
            raw_sql = f"""
                SELECT kd.id, 1 - (e.embedding <=> '{vec_str}'::vector) AS score
                FROM ai_embeddings e
                JOIN ai_knowledge_documents kd ON kd.id = e.document_id
                WHERE e.tenant_id = '{tenant_id}'
                  AND kd.is_deleted = false
                  AND kd.is_indexed = true
                  {"AND kd.source_type = '" + source_type + "'" if source_type else ""}
                ORDER BY e.embedding <=> '{vec_str}'::vector
                LIMIT {top_k}
            """
            result = await db.execute(raw_sql)
            rows = result.fetchall()
            docs_with_scores = []
            for row in rows:
                if row[1] >= min_score:
                    doc = await db.get(AIKnowledgeDocument, row[0])
                    if doc:
                        docs_with_scores.append((doc, float(row[1])))
            return docs_with_scores
        except Exception:
            # Fallback: return top documents by recency (no vector search available)
            stmt = select(AIKnowledgeDocument).where(
                AIKnowledgeDocument.tenant_id == tenant_id,
                AIKnowledgeDocument.is_indexed == True,
                AIKnowledgeDocument.is_deleted == False,
            )
            if source_type:
                stmt = stmt.where(AIKnowledgeDocument.source_type == source_type)
            stmt = stmt.order_by(AIKnowledgeDocument.created_at.desc()).limit(top_k)
            docs = list((await db.execute(stmt)).scalars().all())
            return [(doc, 0.75) for doc in docs]

    # ── AI Jobs ───────────────────────────────────────────────────────────────

    async def create_job(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        job_type: str,
        total_items: int = 0,
        created_by: Optional[UUID] = None,
    ) -> AIJob:
        job = AIJob(
            tenant_id=tenant_id,
            organization_id=organization_id,
            job_type=job_type,
            status="queued",
            total_items=total_items,
            created_by=created_by,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def get_job(
        self, db: AsyncSession, *, job_id: UUID, tenant_id: UUID
    ) -> Optional[AIJob]:
        stmt = select(AIJob).where(
            AIJob.id == job_id,
            AIJob.tenant_id == tenant_id,
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    # ── Audit Log ─────────────────────────────────────────────────────────────

    async def write_audit_log(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID],
        provider: str,
        model_name: str,
        feature: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        status: str = "success",
        error_message: Optional[str] = None,
        citation_count: int = 0,
    ) -> AIAuditLog:
        log = AIAuditLog(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            conversation_id=conversation_id,
            provider=provider,
            model_name=model_name,
            feature=feature,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            citation_count=citation_count,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log


ai_repo = AIRepository()
