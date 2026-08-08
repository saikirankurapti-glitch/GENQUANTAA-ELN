import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

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
        self, *, obj_in: InventoryItemCreate, tenant_id: UUID, current_user: User
    ) -> InventoryItem:
        """Create a new inventory item ensuring item_code is unique per tenant."""
        # 1. Validate Code Uniqueness
        existing = await inventory_repo.get_by_code(item_code=obj_in.item_code, tenant_id=tenant_id)
        if existing:
            raise DuplicateInventoryItemCode(
                f"Inventory item code '{obj_in.item_code}' already exists in this tenant workspace."
            )

        item = await inventory_repo.create(
            obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"InventoryService: Created new item {item.id} (Code: {item.sku})")
        return item

    async def get_item(
        self, *, item_id: UUID, tenant_id: UUID
    ) -> InventoryItem:
        """Retrieve an item, raising NotFound if missing or deleted."""
        item = await inventory_repo.get_by_id(id=item_id, tenant_id=tenant_id, include_details=True)
        if not item:
            raise InventoryItemNotFound(f"Inventory item with ID {item_id} not found.")
        return item

    async def update_item(
        self,
        *,
        item_id: UUID,
        obj_in: InventoryItemUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> InventoryItem:
        """Update item details (metadata only). Cannot update current_stock directly."""
        item = await self.get_item(item_id=item_id, tenant_id=tenant_id)

        # Code Uniqueness Check if code is being updated
        if obj_in.item_code and obj_in.item_code != item.sku:
            existing = await inventory_repo.get_by_code(item_code=obj_in.item_code, tenant_id=tenant_id)
            if existing:
                raise DuplicateInventoryItemCode(
                    f"Cannot rename code to '{obj_in.item_code}'. It is already in use."
                )

        updated_item = await inventory_repo.update(
            db_obj=item, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"InventoryService: Updated item {item_id}")
        return updated_item

    async def receive_stock(
        self,
        *,
        item_id: UUID,
        req: InventoryReceiveRequest,
        tenant_id: UUID,
        current_user: User
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Receive (add) stock to an inventory item."""
        item = await self.get_item(item_id=item_id, tenant_id=tenant_id)
        if item.status == "archived":
            raise InventoryItemArchivedError("Cannot receive stock into an archived item.")

        updated_item, tx = await inventory_repo.receive_stock(
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
        *,
        item_id: UUID,
        req: InventoryIssueRequest,
        tenant_id: UUID,
        current_user: User
    ) -> Tuple[InventoryItem, InventoryTransaction]:
        """Issue/consume stock quantity from an inventory item."""
        item = await self.get_item(item_id=item_id, tenant_id=tenant_id)
        if item.status == "archived":
            raise InventoryItemArchivedError("Cannot issue stock from an archived item.")

        # Check Stock Balance
        if req.quantity > item.current_stock:
            raise InsufficientStockError(
                f"Requested issue quantity ({req.quantity} {item.unit}) exceeds available stock balance ({item.current_stock} {item.unit})."
            )

        updated_item, tx = await inventory_repo.issue_stock(
            item=item,
            quantity=req.quantity,
            remarks=req.remarks,
            current_user_id=current_user.id,
        )
        logger.info(f"InventoryService: Issued {req.quantity} {item.unit} from item {item_id}")
        return updated_item, tx

    async def delete_item(
        self, *, item_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete an inventory item."""
        success = await inventory_repo.soft_delete(
            id=item_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise InventoryItemNotFound(f"Inventory item {item_id} not found.")
        logger.info(f"InventoryService: Soft deleted item {item_id}")
        return True

    async def get_inventory_items(
        self, *, tenant_id: UUID, filters: InventoryFilter, pagination: InventoryPagination
    ) -> Tuple[List[dict], int]:
        """Fetch a paginated list of inventory items matching the applied filters."""
        return await inventory_repo.get_multi(
            tenant_id=tenant_id,
            category_id=filters.category_id,
            supplier_id=filters.supplier_id,
            storage_location_id=filters.storage_location_id,
            status=filters.status,
            is_low_stock=filters.is_low_stock,
            search=filters.search,
            skip=(pagination.page - 1) * pagination.page_size,
            limit=pagination.page_size,
        )


inventory_service = InventoryService()
