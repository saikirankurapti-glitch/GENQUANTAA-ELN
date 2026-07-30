import logging
from uuid import UUID
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import require_permission, get_current_active_user
from app.schemas.rbac import PermissionCreate, PermissionUpdate, PermissionListResponse, PermissionRead
from app.services.rbac.permission_service import permission_service
from app.services.rbac.exceptions import (
    PermissionNotFound,
    PermissionAlreadyExists,
    InvalidPermissionCode,
    ValidationError
)
from app.models.identity import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Permission",
    description="Creates a new global permission following the 'module.resource.action' naming convention."
)
async def create_permission(
    *,
    db: AsyncSession = Depends(get_db),
    permission_in: PermissionCreate,
    current_user: User = Depends(require_permission("rbac.permission.create"))
) -> Any:
    """Create a new global Permission."""
    try:
        new_perm = await permission_service.create_permission(db, obj_in=permission_in)
        return new_perm
    except PermissionAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (InvalidPermissionCode, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/",
    response_model=PermissionListResponse,
    summary="List all Permissions",
    description="Retrieves a list of all permissions registered in the global system registry."
)
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("rbac.permission.read"))
) -> Any:
    """List all global permissions."""
    permissions = await permission_service.list_permissions(db)
    return {"items": permissions, "total": len(permissions)}

@router.get(
    "/search",
    response_model=PermissionListResponse,
    summary="Search Permissions",
    description="Search permissions via full-text matching against code, description, module, resource, or action."
)
async def search_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    query: str = Query(..., description="Search query string"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("rbac.permission.read"))
) -> Any:
    """Search global permissions by a substring query."""
    permissions, total = await permission_service.search_permissions(
        db, 
        query=query, 
        page=page, 
        page_size=page_size
    )
    return {"items": permissions, "total": total}

@router.get(
    "/{permission_id}",
    response_model=PermissionRead,
    summary="Get Permission by ID",
    description="Fetch the exact details of a single global permission using its UUID."
)
async def get_permission(
    *,
    db: AsyncSession = Depends(get_db),
    permission_id: UUID,
    current_user: User = Depends(require_permission("rbac.permission.read"))
) -> Any:
    """Get a specific global permission by its ID."""
    try:
        return await permission_service.get_permission(db, id=permission_id)
    except PermissionNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put(
    "/{permission_id}",
    response_model=PermissionRead,
    summary="Update an existing Permission",
    description="Update a global permission's metadata. Code validation rules will apply to updates."
)
async def update_permission(
    *,
    db: AsyncSession = Depends(get_db),
    permission_id: UUID,
    permission_in: PermissionUpdate,
    current_user: User = Depends(require_permission("rbac.permission.update"))
) -> Any:
    """Update a specific global permission."""
    try:
        return await permission_service.update_permission(db, id=permission_id, obj_in=permission_in)
    except PermissionNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (InvalidPermissionCode, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/{permission_id}",
    response_model=PermissionRead,
    summary="Delete a Permission",
    description="Hard delete a permission from the global registry."
)
async def delete_permission(
    *,
    db: AsyncSession = Depends(get_db),
    permission_id: UUID,
    current_user: User = Depends(require_permission("rbac.permission.delete"))
) -> Any:
    """Delete a global permission."""
    try:
        return await permission_service.delete_permission(db, id=permission_id)
    except PermissionNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
