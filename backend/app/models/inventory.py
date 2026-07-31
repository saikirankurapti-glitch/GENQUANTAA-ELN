from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Float, Integer, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

class InventoryCategory(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "inventory_categories"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

class InventorySupplier(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "inventory_suppliers"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class InventoryLocation(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "inventory_locations"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    room: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

class InventoryItem(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("inventory_categories.id", ondelete="RESTRICT"), nullable=False)
    supplier_id: Mapped[Optional[UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("inventory_suppliers.id", ondelete="SET NULL"), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="pcs", nullable=False)

class InventoryBatch(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "inventory_batches"

    item_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

class InventoryTransaction(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "inventory_transactions"

    item_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity_changed: Mapped[float] = mapped_column(Float, nullable=False)
