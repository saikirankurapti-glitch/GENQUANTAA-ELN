import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Boolean, String, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin

@declarative_mixin
class UUIDMixin:
    """Provides a standardized UUID primary key for all models."""
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

@declarative_mixin
class TimestampMixin:
    """Provides created_at and updated_at timestamps for all models."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

@declarative_mixin
class SoftDeleteMixin:
    """Provides soft-delete capabilities required by ALCOA+ and GxP standards."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

@declarative_mixin
class TenantMixin:
    """Provides multi-tenancy data isolation required for the enterprise platform."""
    # Note: This creates a hard dependency on a 'tenants' table existing in the database.
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )

@declarative_mixin
class AuditMixin:
    """Provides traceability for who created or updated a record."""
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
