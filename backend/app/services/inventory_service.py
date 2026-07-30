import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_inventory import inventory_repo
from app.models.identity import User
from app.models.inventory import InventoryItem, InventoryTransaction
from app.schemas.inventory import (
    InventoryFilter,
    InventoryIssueRequest,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryPagination,
    InventoryReceiveRequest,
)

logger = logging.getLogger(__name__)


# Domain Exceptions
class InventoryItemNotFound(Exception):
    pass


class DuplicateInventoryItemCode(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class InventoryItemArchivedError(Exception):
    pass


class ExpiredInventoryError(Exception):
    pass


class InventoryService:
    """Service layer enforcing inventory stock checks, issue limits, low-stock warnings, and transaction ledgers."""

    async def create_item(
        self, db: AsyncSession, *, obj_in: InventoryItemCreate, tenant_id: UUID, current_user: User
    ) -> InventoryItem:
        """Create a new inventory item ensuring item_code is unique per tenant."""
        # 1. Validate Code Uniqueness
        existing = await inventory_repo.get_by_code(db, item_code=obj_in.item_code, tenant_id=tenant_id)
        if existing:
            raise DuplicateInventoryItemCode(
                f"Inventory item code '{obj_in.item_code}' already exists in this tenant workspace."
            )

        item = await inventory_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"InventoryService: Registered item '{item.item_code}' (ID: {item.id})")
        return item

    async def get_item(
        self, db: AsyncSession, *, item_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> InventoryItem:
        """Fetch inventory item by ID or raise InventoryItemNotFound."""
        item = await inventory_repo.get_by_id(
            db, id=item_id, tenant_id=tenant_id, include_details=include_details
        )
        if not item:
            raise InventoryItemNotFound(f"Inventory item {item_id} not found.")
        return item

    async def update_item(
        self,
        db: AsyncSession,
        *,
        item_id: UUID,
        obj_in: InventoryItemUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> InventoryItem:
        """Update inventory item details."""
        item = await self.get_item(db, item_id=item_id, tenant_id=tenant_id)
        if item.status == "archived":
            raise InventoryItemArchivedError("Cannot update an archived inventory item.")

        updated_item = await inventory_repo.update(
            db, db_obj=item, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"InventoryService: Updated item {item_id}")
        return updated_item

    async def receive_stock(
        self,
        db: AsyncSession,
        *,
        item_id: UUID,
        req: InventoryReceiveRequest,
        tenant_id: UUID,
        current_user: User
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Receive new stock quantity into an inventory item."""
        item = await self.get_item(db, item_id=item_id, tenant_id=tenant_id)
        if item.status == "archived":
            raise InventoryItemArchivedError("Cannot receive stock for an archived item.")

        updated_item, tx = await inventory_repo.receive_stock(
            db,
            item=item,
            quantity=req.quantity,
            lot_number=req.lot_number,
            expiry_date=req.expiry_date,
            remarks=req.remarks,
            current_user_id=current_user.id,
        )
        logger.info(f"InventoryService: Received {req.quantity} {item.unit} for item {item_id}")
        return updated_item, tx

    async def issue_stock(
        self,
        db: AsyncSession,
        *,
        item_id: UUID,
        req: InventoryIssueRequest,
        tenant_id: UUID,
        current_user: User
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Issue/consume stock quantity from an inventory item."""
        item = await self.get_item(db, item_id=item_id, tenant_id=tenant_id)
        if item.status == "archived":
            raise InventoryItemArchivedError("Cannot issue stock from an archived item.")

        # Check Expiry
        if item.expiry_date and item.expiry_date < date.today():
            raise ExpiredInventoryError(f"Inventory item '{item.item_code}' expired on {item.expiry_date} and cannot be issued.")

        # Check Stock Balance
        if req.quantity > item.current_stock:
            raise InsufficientStockError(
                f"Requested issue quantity ({req.quantity} {item.unit}) exceeds available stock balance ({item.current_stock} {item.unit})."
            )

        updated_item, tx = await inventory_repo.issue_stock(
            db,
            item=item,
            quantity=req.quantity,
            remarks=req.remarks,
            current_user_id=current_user.id,
        )
        logger.info(f"InventoryService: Issued {req.quantity} {item.unit} from item {item_id}")
        return updated_item, tx

    async def delete_item(
        self, db: AsyncSession, *, item_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete an inventory item."""
        success = await inventory_repo.soft_delete(
            db, id=item_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise InventoryItemNotFound(f"Inventory item {item_id} not found.")
        logger.info(f"InventoryService: Soft deleted item {item_id}")
        return True

    async def list_items(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: InventoryFilter,
        pagination: InventoryPagination
    ) -> Tuple[List[InventoryItem], int]:
        """List inventory items with filtering and pagination."""
        return await inventory_repo.list_items(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

    async def list_transactions(
        self, db: AsyncSession, *, item_id: UUID, tenant_id: UUID
    ) -> List[InventoryTransaction]:
        """Fetch transaction ledger for an inventory item."""
        await self.get_item(db, item_id=item_id, tenant_id=tenant_id, include_details=False)
        return await inventory_repo.list_transactions(db, item_id=item_id)


inventory_service = InventoryService()
