import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    """Async Repository handling data access for Inventory entities with tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: InventoryItemCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> InventoryItem:
        """Create a new InventoryItem record."""
        initial_stock = obj_in.initial_stock
        item = InventoryItem(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            category_id=obj_in.category_id,
            supplier_id=obj_in.supplier_id,
            storage_location_id=obj_in.storage_location_id,
            item_code=obj_in.item_code,
            item_name=obj_in.item_name,
            unit=obj_in.unit,
            minimum_stock=obj_in.minimum_stock,
            current_stock=initial_stock,
            reorder_level=obj_in.reorder_level,
            lot_number=obj_in.lot_number,
            expiry_date=obj_in.expiry_date,
            status="available" if initial_stock > 0 else "out_of_stock",
            metadata_json=obj_in.metadata_json,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(item)
        await db.flush()

        # Log initial stock transaction if initial_stock > 0
        if initial_stock > 0:
            tx = InventoryTransaction(
                inventory_item_id=item.id,
                transaction_type="receive",
                quantity=initial_stock,
                performed_by=current_user_id,
                remarks="Initial inventory stock check-in.",
            )
            db.add(tx)

            # Create initial batch lot if lot_number supplied
            if obj_in.lot_number:
                batch = InventoryBatch(
                    inventory_item_id=item.id,
                    lot_number=obj_in.lot_number,
                    batch_quantity=initial_stock,
                    expiry_date=obj_in.expiry_date,
                    status="active",
                )
                db.add(batch)

        await db.commit()
        await db.refresh(item)
        return item

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[InventoryItem]:
        """Fetch InventoryItem by ID within tenant scope."""
        stmt = select(InventoryItem).where(
            InventoryItem.id == id,
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(InventoryItem.category),
                selectinload(InventoryItem.supplier),
                selectinload(InventoryItem.storage_location),
                selectinload(InventoryItem.batches),
                selectinload(InventoryItem.transactions),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, item_code: str, tenant_id: UUID
    ) -> Optional[InventoryItem]:
        """Fetch InventoryItem by item_code within tenant scope."""
        stmt = select(InventoryItem).where(
            InventoryItem.item_code == item_code.upper(),
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: InventoryItem,
        obj_in: InventoryItemUpdate,
        current_user_id: Optional[UUID] = None
    ) -> InventoryItem:
        """Update existing InventoryItem attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def receive_stock(
        self,
        db: AsyncSession,
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
            item.status = "available"
        elif item.current_stock > 0:
            item.status = "low_stock"

        item.updated_by = current_user_id
        item.updated_at = datetime.now(timezone.utc)
        db.add(item)

        tx = InventoryTransaction(
            inventory_item_id=item.id,
            transaction_type="receive",
            quantity=quantity,
            performed_by=current_user_id,
            remarks=remarks or f"Received {quantity} {item.unit} into stock.",
        )
        db.add(tx)

        if lot_number:
            batch = InventoryBatch(
                inventory_item_id=item.id,
                lot_number=lot_number,
                batch_quantity=quantity,
                expiry_date=expiry_date,
                status="active",
            )
            db.add(batch)

        await db.commit()
        await db.refresh(item)
        await db.refresh(tx)
        return item, tx

    async def issue_stock(
        self,
        db: AsyncSession,
        *,
        item: InventoryItem,
        quantity: float,
        remarks: Optional[str] = None,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Issue/consume stock, update current_stock, and log transaction ledger."""
        item.current_stock -= quantity
        if item.current_stock == 0:
            item.status = "out_of_stock"
        elif item.current_stock <= item.reorder_level:
            item.status = "low_stock"

        item.updated_by = current_user_id
        item.updated_at = datetime.now(timezone.utc)
        db.add(item)

        tx = InventoryTransaction(
            inventory_item_id=item.id,
            transaction_type="issue",
            quantity=-quantity,
            performed_by=current_user_id,
            remarks=remarks or f"Issued {quantity} {item.unit} from stock.",
        )
        db.add(tx)

        await db.commit()
        await db.refresh(item)
        await db.refresh(tx)
        return item, tx

    async def archive(
        self, db: AsyncSession, *, item_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[InventoryItem]:
        """Archive an InventoryItem."""
        item = await self.get_by_id(db, id=item_id, tenant_id=tenant_id)
        if not item:
            return None

        item.status = "archived"
        item.archived_at = datetime.now(timezone.utc)
        item.updated_by = current_user_id
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def restore(
        self, db: AsyncSession, *, item_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[InventoryItem]:
        """Restore an archived InventoryItem."""
        item = await self.get_by_id(db, id=item_id, tenant_id=tenant_id)
        if not item:
            return None

        item.status = "available" if item.current_stock > 0 else "out_of_stock"
        item.archived_at = None
        item.updated_by = current_user_id
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft delete InventoryItem."""
        item = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not item:
            return False

        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        item.deleted_by = current_user_id
        db.add(item)
        await db.commit()
        return True

    async def list_items(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: InventoryFilter,
        pagination: InventoryPagination
    ) -> Tuple[List[InventoryItem], int]:
        """List and search InventoryItems with filtering and pagination."""
        query = select(InventoryItem).where(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_deleted == False
        )

        if filter_params.category_id:
            query = query.where(InventoryItem.category_id == filter_params.category_id)
        if filter_params.supplier_id:
            query = query.where(InventoryItem.supplier_id == filter_params.supplier_id)
        if filter_params.storage_location_id:
            query = query.where(InventoryItem.storage_location_id == filter_params.storage_location_id)
        if filter_params.status:
            query = query.where(InventoryItem.status == filter_params.status)
        if filter_params.is_low_stock is True:
            query = query.where(InventoryItem.current_stock <= InventoryItem.reorder_level)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    InventoryItem.item_code.ilike(pattern),
                    InventoryItem.item_name.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(InventoryItem, pagination.sort_by, InventoryItem.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def list_transactions(
        self, db: AsyncSession, *, item_id: UUID
    ) -> List[InventoryTransaction]:
        """Fetch stock transaction history for an inventory item."""
        stmt = (
            select(InventoryTransaction)
            .where(InventoryTransaction.inventory_item_id == item_id)
            .order_by(InventoryTransaction.performed_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


inventory_repo = InventoryRepository()
