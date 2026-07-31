from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class InstrumentType(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "instrument_types"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

class Instrument(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "instruments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument_type_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("instrument_types.id", ondelete="RESTRICT"), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class InstrumentCalibration(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "instrument_calibrations"

    instrument_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="passed", nullable=False)

class InstrumentMaintenance(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "instrument_maintenances"

    instrument_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

class InstrumentReservation(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "instrument_reservations"

    instrument_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class InstrumentUsage(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "instrument_usages"

    instrument_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class InstrumentAttachment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "instrument_attachments"

    instrument_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
