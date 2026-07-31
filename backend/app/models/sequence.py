from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Text, Integer, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class Sequence(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "sequences"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence_type: Mapped[str] = mapped_column(String(32), nullable=False) # DNA, RNA, AMINO
    sequence_data: Mapped[str] = mapped_column(Text, nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False)

class SequenceVersion(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sequence_versions"

    sequence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sequences.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_data: Mapped[str] = mapped_column(Text, nullable=False)

class SequenceAnnotation(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sequence_annotations"

    sequence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sequences.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    start_pos: Mapped[int] = mapped_column(Integer, nullable=False)
    end_pos: Mapped[int] = mapped_column(Integer, nullable=False)

class SequenceAttachment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sequence_attachments"

    sequence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sequences.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

class SequenceAnalysisResult(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sequence_analysis_results"

    sequence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sequences.id", ondelete="CASCADE"), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(64), nullable=False)
    result_data: Mapped[dict] = mapped_column(JSON, nullable=False)
