import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from app.models.inventory import (
    InventoryBatch,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventorySupplier,
    InventoryTransaction,
)
from app.schemas.inventory import (
    InventoryFilter,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryPagination,
)

logger = logging.getLogger(__name__)


class InventoryRepository:
    """Async Repository handling data access for Inventory entities with tenant isolation (Beanie version)."""

    async def create(
        self,
        *,
        obj_in: InventoryItemCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> InventoryItem:
        """Create a new InventoryItem record."""
        initial_stock = obj_in.initial_stock
        item = InventoryItem(
            tenant_id=tenant_id,
            category_id=obj_in.category_id,
            supplier_id=obj_in.supplier_id,
            location_id=obj_in.storage_location_id,
            name=obj_in.item_name,
            sku=obj_in.item_code,
            unit=obj_in.unit,
            current_stock=initial_stock,
            reorder_level=obj_in.reorder_level,
            status="in_stock" if initial_stock > 0 else "out_of_stock",
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await item.insert()

        # Log initial stock transaction if initial_stock > 0
        if initial_stock > 0:
            tx = InventoryTransaction(
                item_id=item.id,
                transaction_type="receive",
                quantity=initial_stock,
                performed_by=current_user_id,
                remarks="Initial inventory stock check-in.",
            )
            await tx.insert()

            # Create initial batch lot if lot_number supplied
            if obj_in.lot_number:
                batch = InventoryBatch(
                    item_id=item.id,
                    batch_number=obj_in.lot_number,
                    quantity=initial_stock,
                    expiry_date=datetime.combine(obj_in.expiry_date, datetime.min.time()) if obj_in.expiry_date else None,
                    status="active",
                )
                await batch.insert()

        return item

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[InventoryItem]:
        """Fetch InventoryItem by ID within tenant scope."""
        return await InventoryItem.find_one(
            InventoryItem.id == id,
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_deleted == False
        )

    async def get_by_code(
        self, *, item_code: str, tenant_id: UUID
    ) -> Optional[InventoryItem]:
        """Fetch InventoryItem by item_code within tenant scope."""
        return await InventoryItem.find_one(
            InventoryItem.sku == item_code.upper(),
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_deleted == False
        )

    async def update(
        self,
        *,
        db_obj: InventoryItem,
        obj_in: InventoryItemUpdate,
        current_user_id: Optional[UUID] = None
    ) -> InventoryItem:
        """Update existing InventoryItem attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        if 'item_code' in update_data:
            db_obj.sku = update_data['item_code']
        if 'item_name' in update_data:
            db_obj.name = update_data['item_name']
        if 'storage_location_id' in update_data:
            db_obj.location_id = update_data['storage_location_id']
            
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()
        return db_obj

    async def receive_stock(
        self,
        *,
        item: InventoryItem,
        quantity: float,
        lot_number: Optional[str] = None,
        expiry_date: Optional[date] = None,
        remarks: Optional[str] = None,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Receive new stock, update current_stock, and log transaction ledger."""
        item.current_stock += quantity
        if item.current_stock > item.reorder_level:
            item.status = "in_stock"
        elif item.current_stock > 0:
            item.status = "low_stock"

        item.updated_at = datetime.now(timezone.utc)
        await item.save()

        tx = InventoryTransaction(
            item_id=item.id,
            transaction_type="receive",
            quantity=quantity,
            performed_by=current_user_id,
            remarks=remarks,
        )
        await tx.insert()

        if lot_number:
            batch = InventoryBatch(
                item_id=item.id,
                batch_number=lot_number,
                quantity=quantity,
                expiry_date=datetime.combine(expiry_date, datetime.min.time()) if expiry_date else None,
                status="active",
            )
            await batch.insert()

        return item, tx

    async def issue_stock(
        self,
        *,
        item: InventoryItem,
        quantity: float,
        remarks: Optional[str] = None,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Issue stock, decrement current_stock, and log transaction ledger."""
        item.current_stock -= quantity
        if item.current_stock <= 0:
            item.current_stock = 0
            item.status = "out_of_stock"
        elif item.current_stock <= item.reorder_level:
            item.status = "low_stock"

        item.updated_at = datetime.now(timezone.utc)
        await item.save()

        tx = InventoryTransaction(
            item_id=item.id,
            transaction_type="issue",
            quantity=quantity,
            performed_by=current_user_id,
            remarks=remarks,
        )
        await tx.insert()
        return item, tx

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft delete an item by marking is_deleted=True."""
        item = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not item:
            return False
        item.is_deleted = True
        item.updated_at = datetime.now(timezone.utc)
        await item.save()
        return True

    async def get_multi(
        self,
        *,
        tenant_id: UUID,
        category_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        storage_location_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_low_stock: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        """Fetch paginated items with filtering."""
        query = InventoryItem.find(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_deleted == False
        )

        if category_id:
            query = query.find(InventoryItem.category_id == category_id)
        if supplier_id:
            query = query.find(InventoryItem.supplier_id == supplier_id)
        if storage_location_id:
            query = query.find(InventoryItem.location_id == storage_location_id)
        if status:
            query = query.find(InventoryItem.status == status)
        if is_low_stock:
            query = query.find(InventoryItem.current_stock <= InventoryItem.reorder_level)
            
        if search:
            query = query.find({"$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"sku": {"$regex": search, "$options": "i"}}
            ]})

        total = await query.count()
        items = await query.sort(-InventoryItem.created_at).skip(skip).limit(limit).to_list()
        
        # Manually map to dicts to match Pydantic schemas expected by the API
        mapped_items = []
        for i in items:
            mapped = {
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": tenant_id,
                "category_id": i.category_id,
                "supplier_id": i.supplier_id,
                "storage_location_id": i.location_id,
                "item_code": i.sku,
                "item_name": i.name,
                "unit": i.unit,
                "current_stock": i.current_stock,
                "minimum_stock": 0,
                "reorder_level": i.reorder_level,
                "status": i.status,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
                "is_low_stock": i.current_stock <= i.reorder_level,
            }
            mapped_items.append(mapped)

        return mapped_items, total


inventory_repo = InventoryRepository()
