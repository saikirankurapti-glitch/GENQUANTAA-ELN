from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4

class InventoryCategory(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inventory_categories"

class InventorySupplier(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    contact_email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inventory_suppliers"

class InventoryLocation(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    room: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inventory_locations"

class InventoryItem(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    category_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    name: str
    sku: str
    status: str = "in_stock"
    current_stock: float = 0.0
    reorder_level: float = 5.0
    unit: str = "pcs"
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inventory_items"

class InventoryBatch(Document):
    id: UUID = Field(default_factory=uuid4)
    item_id: UUID
    batch_number: str
    quantity: float
    expiry_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inventory_batches"

class InventoryTransaction(Document):
    id: UUID = Field(default_factory=uuid4)
    item_id: UUID
    user_id: UUID
    transaction_type: str
    quantity_changed: float
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "inventory_transactions"
