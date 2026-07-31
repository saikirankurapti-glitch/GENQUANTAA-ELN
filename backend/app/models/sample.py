from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Float, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class SampleType(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sample_types"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

class SampleStorageLocation(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sample_storage_locations"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    freezer_unit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shelf: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

class Sample(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "samples"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_code: Mapped[str] = mapped_column(String(64), nullable=False)
    sample_type_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sample_types.id", ondelete="RESTRICT"), nullable=False)
    location_id: Mapped[Optional[UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("sample_storage_locations.id", ondelete="SET NULL"), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="mL", nullable=False)

class SampleChainOfCustody(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sample_chain_of_custody"

    sample_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)

class SampleAttachment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sample_attachments"

    sample_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

class SampleAliquot(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "sample_aliquots"

    parent_sample_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    aliquot_code: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
