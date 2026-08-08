import math
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

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
        pagination_req = InventoryPagination(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        
        items, total = await inventory_service.get_inventory_items(
            tenant_id=current_tenant.id, filters=filter_params, pagination=pagination_req
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return InventoryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        import logging
        logging.error(f"Error fetching inventory: {e}")
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
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search inventory items."""
    try:
        filter_params = InventoryFilter(search=q)
        pagination_req = InventoryPagination(
            page=page, page_size=page_size, sort_by="created_at", sort_order="desc"
        )
        
        items, total = await inventory_service.get_inventory_items(
            tenant_id=current_tenant.id, filters=filter_params, pagination=pagination_req
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return InventoryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        import logging
        logging.error(f"Error searching inventory: {e}")
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
)
async def create_inventory_item(
    *,
    obj_in: InventoryItemCreate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Create a new inventory item."""
    try:
        item = await inventory_service.create_item(
            obj_in=obj_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "category_id": item.category_id,
            "supplier_id": item.supplier_id,
            "storage_location_id": item.location_id,
            "item_code": item.sku,
            "item_name": item.name,
            "unit": item.unit,
            "current_stock": item.current_stock,
            "minimum_stock": 0,
            "reorder_level": item.reorder_level,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    except DuplicateInventoryItemCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{item_id}",
    response_model=InventoryItemRead,
    status_code=status.HTTP_200_OK,
    summary="Get Inventory Item",
)
async def get_inventory_item(
    item_id: UUID,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Get inventory item details."""
    try:
        item = await inventory_service.get_item(
            item_id=item_id, tenant_id=current_tenant.id
        )
        reorder_level = getattr(item, "reorder_level", 0.0) or 0.0
        current_stock = getattr(item, "current_stock", 0.0) or 0.0
        minimum_stock = getattr(item, "minimum_stock", 0.0) or 0.0
        is_low_stock = current_stock <= reorder_level if reorder_level > 0 else False
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "organization_id": getattr(item, "organization_id", item.tenant_id),
            "category_id": item.category_id,
            "supplier_id": item.supplier_id,
            "storage_location_id": getattr(item, "location_id", None),
            "item_code": getattr(item, "sku", getattr(item, "item_code", "UNKNOWN")),
            "item_name": getattr(item, "name", getattr(item, "item_name", "")),
            "unit": item.unit,
            "current_stock": current_stock,
            "minimum_stock": minimum_stock,
            "reorder_level": reorder_level,
            "is_low_stock": is_low_stock,
            "status": item.status,
            "lot_number": getattr(item, "lot_number", None),
            "expiry_date": getattr(item, "expiry_date", None),
            "metadata_json": getattr(item, "metadata_json", {}) or {},
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



@router.put(
    "/{item_id}",
    response_model=InventoryItemRead,
    status_code=status.HTTP_200_OK,
    summary="Update Inventory Item",
)
async def update_inventory_item(
    item_id: UUID,
    obj_in: InventoryItemUpdate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Update inventory item."""
    try:
        item = await inventory_service.update_item(
            item_id=item_id,
            obj_in=obj_in,
            tenant_id=current_tenant.id,
            current_user=current_user,
        )
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "category_id": item.category_id,
            "supplier_id": item.supplier_id,
            "storage_location_id": item.location_id,
            "item_code": item.sku,
            "item_name": item.name,
            "unit": item.unit,
            "current_stock": item.current_stock,
            "minimum_stock": 0,
            "reorder_level": item.reorder_level,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateInventoryItemCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Inventory Item",
)
async def delete_inventory_item(
    item_id: UUID,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Delete inventory item."""
    try:
        await inventory_service.delete_item(
            item_id=item_id, tenant_id=current_tenant.id, current_user=current_user
        )
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{item_id}/receive",
    response_model=InventoryItemRead,
    status_code=status.HTTP_200_OK,
    summary="Receive Stock",
)
async def receive_inventory_stock(
    item_id: UUID,
    req: InventoryReceiveRequest,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Receive additional stock for an item."""
    try:
        item, tx = await inventory_service.receive_stock(
            item_id=item_id,
            req=req,
            tenant_id=current_tenant.id,
            current_user=current_user,
        )
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "category_id": item.category_id,
            "supplier_id": item.supplier_id,
            "storage_location_id": item.location_id,
            "item_code": item.sku,
            "item_name": item.name,
            "unit": item.unit,
            "current_stock": item.current_stock,
            "minimum_stock": 0,
            "reorder_level": item.reorder_level,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InventoryItemArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{item_id}/issue",
    response_model=InventoryItemRead,
    status_code=status.HTTP_200_OK,
    summary="Issue Stock",
)
async def issue_inventory_stock(
    item_id: UUID,
    req: InventoryIssueRequest,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Issue or consume stock from an item."""
    try:
        item, tx = await inventory_service.issue_stock(
            item_id=item_id,
            req=req,
            tenant_id=current_tenant.id,
            current_user=current_user,
        )
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "category_id": item.category_id,
            "supplier_id": item.supplier_id,
            "storage_location_id": item.location_id,
            "item_code": item.sku,
            "item_name": item.name,
            "unit": item.unit,
            "current_stock": item.current_stock,
            "minimum_stock": 0,
            "reorder_level": item.reorder_level,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    except InventoryItemNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InventoryItemArchivedError, ExpiredInventoryError, InsufficientStockError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
