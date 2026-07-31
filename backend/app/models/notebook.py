from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class NotebookEntry(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "notebook_entries"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experiment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class NotebookEntryVersion(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "notebook_entry_versions"

    entry_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("notebook_entries.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class NotebookAttachment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "notebook_attachments"

    entry_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("notebook_entries.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

class NotebookComment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "notebook_comments"

    entry_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("notebook_entries.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

class NotebookTag(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "notebook_tags"

    entry_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("notebook_entries.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
