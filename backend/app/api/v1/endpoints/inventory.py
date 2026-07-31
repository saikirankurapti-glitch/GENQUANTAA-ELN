import math
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.inventory import (
    InventoryFilter,
    InventoryIssueRequest,
    InventoryItemCreate,
    InventoryItemDetail,
    InventoryItemRead,
    InventoryItemUpdate,
    InventoryListResponse,
    InventoryPagination,
    InventoryReceiveRequest,
    InventoryTransactionRead,
)
from app.services.inventory_service import (
    DuplicateInventoryItemCode,
    ExpiredInventoryError,
    InsufficientStockError,
    InventoryItemArchivedError,
    InventoryItemNotFound,
    inventory_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=InventoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Inventory Items",
    description="Fetch paginated inventory items for current tenant with filtering and low-stock indicators.",
)
async def list_inventory_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    category_id: Optional[UUID] = Query(None),
    supplier_id: Optional[UUID] = Query(None),
    storage_location_id: Optional[UUID] = Query(None),
    status_param: Optional[str] = Query(None, alias="status"),
    is_low_stock: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    """Paginated inventory listing."""
    try:
        filter_params = InventoryFilter(
            category_id=category_id,
            supplier_id=supplier_id,
            storage_location_id=storage_location_id,
            status=status_param,
            is_low_stock=is_low_stock,
            search=search,
        )
        pagination = InventoryPagination(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items, total = await inventory_service.list_items(
            db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        read_items = []
        for item in items:
            read_obj = InventoryItemRead.model_validate(item)
            read_obj.is_low_stock = item.current_stock <= item.reorder_level
            read_items.append(read_obj)

        return InventoryListResponse(
            items=read_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        return InventoryListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.get(
    "/search",
    response_model=InventoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Inventory Items",
    description="Search inventory items by code or name keyword.",
)
async def search_inventory_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search inventory items."""
    try:
        filter_params = InventoryFilter(search=q)
        pagination = InventoryPagination(page=page, page_size=page_size)
        items, total = await inventory_service.list_items(
            db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        read_items = []
        for item in items:
            read_obj = InventoryItemRead.model_validate(item)
            read_obj.is_low_stock = item.current_stock <= item.reorder_level
            read_items.append(read_obj)

        return InventoryListResponse(
            items=read_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        return InventoryListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )



@router.post(
    "/",
    response_model=InventoryItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Inventory Item",
    description="Register a new inventory reagent, chemical, or consumable item.",
)
async def create_inventory_item(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    item_in: InventoryItemCreate,
) -> Any:
    """Create inventory item."""
    try:
        item = await inventory_service.create_item(
            db, obj_in=item_in, tenant_id=current_tenant.id, current_user=current_user
        )
        read_obj = InventoryItemRead.model_validate(item)
        read_obj.is_low_stock = item.current_stock <= item.reorder_level
        return read_obj
    except DuplicateInventoryItemCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{id}",
    response_model=InventoryItemDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Inventory Item Details",
    description="Fetch inventory item detail including category, location, batches, and transaction history.",
)
async def get_inventory_item(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch inventory item detail."""
    try:
        item = await inventory_service.get_item(
            db, item_id=id, tenant_id=current_tenant.id, include_details=True
        )
        detail = InventoryItemDetail.model_validate(item)
        detail.is_low_stock = item.current_stock <= item.reorder_level
        return detail
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=InventoryItemRead,
    status_code=status.HTTP_200_OK,
    summary="Update Inventory Item",
    description="Update inventory item configuration.",
)
async def update_inventory_item(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    item_in: InventoryItemUpdate,
) -> Any:
    """Update inventory item."""
    try:
        item = await inventory_service.update_item(
            db, item_id=id, obj_in=item_in, tenant_id=current_tenant.id, current_user=current_user
        )
        read_obj = InventoryItemRead.model_validate(item)
        read_obj.is_low_stock = item.current_stock <= item.reorder_level
        return read_obj
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InventoryItemArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Inventory Item",
    description="Soft-delete an inventory item.",
)
async def delete_inventory_item(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Soft delete inventory item."""
    try:
        await inventory_service.delete_item(
            db, item_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/receive",
    response_model=InventoryTransactionRead,
    status_code=status.HTTP_200_OK,
    summary="Receive Stock",
    description="Check in new stock quantity into inventory balance.",
)
async def receive_stock(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    req: InventoryReceiveRequest,
) -> Any:
    """Receive stock."""
    try:
        _, tx = await inventory_service.receive_stock(
            db, item_id=id, req=req, tenant_id=current_tenant.id, current_user=current_user
        )
        return InventoryTransactionRead.model_validate(tx)
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InventoryItemArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{id}/issue",
    response_model=InventoryTransactionRead,
    status_code=status.HTTP_200_OK,
    summary="Issue / Consume Stock",
    description="Issue stock quantity from inventory balance for lab usage.",
)
async def issue_stock(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    req: InventoryIssueRequest,
) -> Any:
    """Issue stock."""
    try:
        _, tx = await inventory_service.issue_stock(
            db, item_id=id, req=req, tenant_id=current_tenant.id, current_user=current_user
        )
        return InventoryTransactionRead.model_validate(tx)
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ExpiredInventoryError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InventoryItemArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{id}/transactions",
    response_model=List[InventoryTransactionRead],
    status_code=status.HTTP_200_OK,
    summary="Get Transaction History",
    description="Fetch stock transaction history for an inventory item.",
)
async def get_transaction_history(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch transaction ledger."""
    try:
        transactions = await inventory_service.list_transactions(
            db, item_id=id, tenant_id=current_tenant.id
        )
        return [InventoryTransactionRead.model_validate(t) for t in transactions]
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
