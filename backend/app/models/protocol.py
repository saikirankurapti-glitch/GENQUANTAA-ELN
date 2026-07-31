from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class Protocol(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "protocols"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    protocol_code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

class ProtocolVersion(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "protocol_versions"

    protocol_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class ProtocolStep(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "protocol_steps"

    protocol_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class ProtocolAttachment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "protocol_attachments"

    protocol_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

class ProtocolApproval(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "protocol_approvals"

    protocol_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False)
    approver_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
