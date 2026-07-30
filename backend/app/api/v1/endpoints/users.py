import math
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
    require_admin,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.identity import (
    UserCreate,
    UserDetailRead,
    UserPagination,
    UserRead,
    UserUpdate,
)
from app.services.identity.exceptions import (
    IdentityException,
    UserAlreadyExists,
    UserNotFound,
)
from app.services.identity.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create User")
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Create a new user within the current tenant."""
    if user_in.tenant_id != current_tenant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create users outside of your assigned tenant scope.",
        )

    try:
        new_user = await user_service.register_user(db, obj_in=user_in)
        return new_user
    except UserAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=UserPagination, summary="List Users")
async def list_users(
    *,
    db: AsyncSession = Depends(get_db),
    organization_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """List users matching criteria within current tenant."""
    status_enum = UserStatus(status_filter) if status_filter else None
    users, total = await user_service.search_users(
        db,
        tenant_id=current_tenant.id,
        organization_id=organization_id,
        status=status_enum,
        is_active=is_active,
        page=page,
        page_size=size,
    )
    pages = math.ceil(total / size) if total > 0 else 1
    return UserPagination(items=users, total=total, page=page, size=size, pages=pages)


@router.get("/search", response_model=UserPagination, summary="Search Users")
async def search_users(
    *,
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., description="Search query string"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Search users by name, email, employee ID, or username."""
    users, total = await user_service.search_users(
        db, tenant_id=current_tenant.id, query=q, page=page, page_size=size
    )
    pages = math.ceil(total / size) if total > 0 else 1
    return UserPagination(items=users, total=total, page=page, size=size, pages=pages)


@router.get("/{user_id}", response_model=UserDetailRead, summary="Get User Details")
async def get_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch user details by ID."""
    try:
        return await user_service.get_user_by_id(
            db, id=user_id, tenant_id=current_tenant.id, include_relations=True
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}", response_model=UserRead, summary="Update User")
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    user_in: UserUpdate,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Update user attributes."""
    try:
        return await user_service.update_user(
            db, id=user_id, tenant_id=current_tenant.id, obj_in=user_in
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", response_model=UserRead, summary="Soft Delete User")
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Soft delete a user account (GxP / Part 11 compliant)."""
    try:
        return await user_service.delete_user(
            db, id=user_id, tenant_id=current_tenant.id, deleted_by=current_user.id
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{user_id}/activate", response_model=UserRead, summary="Activate User")
async def activate_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_permission("identity.user.update")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Activate user account."""
    try:
        return await user_service.activate_user(db, id=user_id, tenant_id=current_tenant.id)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{user_id}/deactivate", response_model=UserRead, summary="Deactivate User")
async def deactivate_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_permission("identity.user.update")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Deactivate user account."""
    try:
        return await user_service.deactivate_user(db, id=user_id, tenant_id=current_tenant.id)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{user_id}/lock", response_model=UserRead, summary="Lock User Account")
async def lock_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_permission("identity.user.update")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Lock user account manually."""
    try:
        return await user_service.lock_user(db, id=user_id, tenant_id=current_tenant.id)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{user_id}/unlock", response_model=UserRead, summary="Unlock User Account")
async def unlock_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_permission("identity.user.update")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Unlock user account and reset failed counters."""
    try:
        return await user_service.unlock_user(db, id=user_id, tenant_id=current_tenant.id)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
