from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryCategoryRead(BaseModel):
    id: UUID = Field(..., description="Category identifier")
    name: str = Field(..., description="Category name (e.g. Chemical Reagents)")
    code: str = Field(..., description="Category code (e.g. CHEM)")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventorySupplierRead(BaseModel):
    id: UUID = Field(..., description="Supplier identifier")
    name: str = Field(..., description="Supplier company name")
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryLocationRead(BaseModel):
    id: UUID = Field(..., description="Location identifier")
    name: str = Field(..., description="Storage location name")
    building: Optional[str] = None
    room: Optional[str] = None
    cabinet_shelf: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryBatchRead(BaseModel):
    id: UUID = Field(..., description="Batch identifier")
    inventory_item_id: UUID = Field(..., description="Parent inventory item identifier")
    lot_number: str = Field(..., description="Lot/Batch manufacture identifier")
    batch_quantity: float = Field(..., description="Batch quantity")
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: str = Field("active", description="Batch status: active, expired, depleted")

    model_config = ConfigDict(from_attributes=True)


class InventoryTransactionRead(BaseModel):
    id: UUID = Field(..., description="Transaction ledger identifier")
    inventory_item_id: UUID = Field(..., description="Associated item identifier")
    transaction_type: str = Field(..., description="Transaction type: receive, issue, adjust, dispose")
    quantity: float = Field(..., description="Quantity delta")
    performed_by: Optional[UUID] = Field(None, description="Performer user identifier")
    performed_at: datetime = Field(..., description="Transaction timestamp")
    remarks: Optional[str] = Field(None, description="Transaction notes")

    model_config = ConfigDict(from_attributes=True)


class InventoryItemBase(BaseModel):
    item_code: str = Field(..., min_length=2, max_length=64, description="Tenant-scoped unique item code (e.g. INV-RGT-001)")
    item_name: str = Field(..., min_length=2, max_length=255, description="Item display name")
    unit: str = Field("units", description="Unit of measure (mL, L, g, kg, boxes, vials, units)")
    minimum_stock: float = Field(default=0.0, ge=0.0, description="Minimum stock threshold")
    reorder_level: float = Field(default=10.0, ge=0.0, description="Reorder alert trigger level")
    lot_number: Optional[str] = Field(None, description="Current batch lot number")
    expiry_date: Optional[date] = Field(None, description="Stock expiration date")
    status: str = Field("available", description="Status: available, low_stock, out_of_stock, expired, archived")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")

    @field_validator("item_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Item code cannot be blank.")
        return v


class InventoryItemCreate(InventoryItemBase):
    organization_id: UUID = Field(..., description="Target Organization identifier")
    category_id: Optional[UUID] = Field(None, description="Category identifier")
    supplier_id: Optional[UUID] = Field(None, description="Supplier identifier")
    storage_location_id: Optional[UUID] = Field(None, description="Storage location identifier")
    initial_stock: float = Field(default=0.0, ge=0.0, description="Initial stock quantity received")


class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = Field(None, min_length=2, max_length=255)
    unit: Optional[str] = None
    minimum_stock: Optional[float] = Field(None, ge=0.0)
    reorder_level: Optional[float] = Field(None, ge=0.0)
    storage_location_id: Optional[UUID] = None
    status: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class InventoryReceiveRequest(BaseModel):
    quantity: float = Field(..., gt=0.0, description="Quantity to receive into stock")
    lot_number: Optional[str] = Field(None, description="Received lot batch number")
    expiry_date: Optional[date] = Field(None, description="Lot expiration date")
    remarks: Optional[str] = Field(None, description="Receiving notes or PO reference")


class InventoryIssueRequest(BaseModel):
    quantity: float = Field(..., gt=0.0, description="Quantity to issue/consume from stock")
    remarks: Optional[str] = Field(None, description="Purpose or Experiment reference notes")


class InventoryItemRead(InventoryItemBase):
    id: UUID = Field(..., description="Inventory item unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: UUID = Field(..., description="Organization identifier")
    category_id: Optional[UUID] = Field(None, description="Category identifier")
    supplier_id: Optional[UUID] = Field(None, description="Supplier identifier")
    storage_location_id: Optional[UUID] = Field(None, description="Storage location identifier")
    current_stock: float = Field(..., description="Current available stock balance")
    is_low_stock: bool = Field(False, description="Computed low-stock alert flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class InventoryItemDetail(InventoryItemRead):
    category: Optional[InventoryCategoryRead] = Field(None, description="Category detail")
    supplier: Optional[InventorySupplierRead] = Field(None, description="Supplier detail")
    storage_location: Optional[InventoryLocationRead] = Field(None, description="Storage location detail")
    batches: List[InventoryBatchRead] = Field(default_factory=list, description="Active batches")
    transactions: List[InventoryTransactionRead] = Field(default_factory=list, description="Stock transaction ledger")


class InventoryItemSummary(BaseModel):
    id: UUID
    item_code: str
    item_name: str
    current_stock: float
    unit: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class InventoryFilter(BaseModel):
    category_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    storage_location_id: Optional[UUID] = None
    status: Optional[str] = None
    is_low_stock: Optional[bool] = Field(None, description="Filter items at or below reorder level")
    search: Optional[str] = Field(None, description="Search keyword matching item_code or item_name")


class InventoryPagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class InventoryListResponse(BaseModel):
    items: List[InventoryItemRead] = Field(default_factory=list, description="Page of inventory items")
    total: int = Field(0, description="Total matching inventory items count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")
