import logging
from uuid import UUID
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    require_permission,
    get_current_active_user,
    get_current_tenant
)
from app.schemas.rbac import RoleCreate, RoleUpdate, RoleListResponse, RoleRead
from app.services.rbac.role_service import role_service
from app.services.rbac.exceptions import (
    RoleNotFound,
    RoleAlreadyExists,
    SystemRoleModificationError,
    SystemRoleDeletionError
)
from app.models.identity import User
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_in: RoleCreate,
    current_user: User = Depends(require_permission("rbac.role.create")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """
    Create a new role within the current tenant scope.
    """
    # Enforce tenant context safety: Ensure the user is trying to create a role in their own tenant
    if role_in.tenant_id != current_tenant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Cannot create roles outside of your assigned tenant."
        )

    try:
        new_role = await role_service.create_role(db, obj_in=role_in)
        return new_role
    except RoleAlreadyExists as e:
        logger.warning(f"Role creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("/", response_model=RoleListResponse)
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("rbac.role.read")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """
    List all active roles within the current tenant.
    """
    roles = await role_service.list_roles(db, tenant_id=current_tenant.id)
    return {"items": roles, "total": len(roles)}

@router.get("/search", response_model=RoleListResponse)
async def search_roles(
    *,
    db: AsyncSession = Depends(get_db),
    query: str = Query(..., description="Search query string"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("rbac.role.read")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """
    Search for roles by name, code, or description.
    """
    roles, total = await role_service.search_roles(
        db, 
        tenant_id=current_tenant.id, 
        query=query, 
        page=page, 
        page_size=page_size
    )
    return {"items": roles, "total": total}

@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    current_user: User = Depends(require_permission("rbac.role.read")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """
    Get a specific role by its ID.
    """
    try:
        return await role_service.get_role(db, id=role_id, tenant_id=current_tenant.id)
    except RoleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{role_id}", response_model=RoleRead)
async def update_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    role_in: RoleUpdate,
    current_user: User = Depends(require_permission("rbac.role.update")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """
    Update a specific role. Prevents updating system roles.
    """
    try:
        return await role_service.update_role(db, id=role_id, tenant_id=current_tenant.id, obj_in=role_in)
    except RoleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RoleAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SystemRoleModificationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{role_id}", response_model=RoleRead)
async def delete_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    current_user: User = Depends(require_permission("rbac.role.delete")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """
    Soft delete a role. Prevents deleting system roles.
    """
    try:
        return await role_service.delete_role(db, id=role_id, tenant_id=current_tenant.id)
    except RoleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SystemRoleDeletionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
