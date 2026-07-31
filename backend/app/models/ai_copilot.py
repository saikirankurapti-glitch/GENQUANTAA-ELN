from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Text, Integer, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class AIConversation(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_conversations"

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New AI Chat", nullable=False)

class AIMessage(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_messages"

    conversation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[str] = mapped_column(String(32), nullable=False) # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

class AIPromptTemplate(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_prompt_templates"

    title: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

class AIKnowledgeDocument(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_knowledge_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

class AIEmbedding(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_embeddings"

    document_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("ai_knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

class AIJob(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_jobs"

    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

class AIAuditLog(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "ai_audit_logs"

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
