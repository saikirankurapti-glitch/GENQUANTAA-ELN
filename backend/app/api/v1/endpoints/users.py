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
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """List users matching criteria within current tenant live from database."""
    from app.models.identity import UserProfile, UserRole
    query = {"is_deleted": False}
    if search and search.strip():
        s = search.strip()
        query["$or"] = [
            {"username": {"$regex": s, "$options": "i"}},
            {"email": {"$regex": s, "$options": "i"}},
            {"first_name": {"$regex": s, "$options": "i"}},
            {"last_name": {"$regex": s, "$options": "i"}},
        ]
    
    total = await User.find(query).count()
    skip = (page - 1) * size
    users_list = await User.find(query).skip(skip).limit(size).to_list()

    items = []
    for u in users_list:
        u_dict = u.model_dump()
        profile = await UserProfile.find_one({"user_id": u.id})
        roles = await UserRole.find({"user_id": u.id, "is_active": True}).to_list()
        u_dict["profile"] = profile.model_dump() if profile else None
        u_dict["roles"] = [r.model_dump() for r in roles]
        items.append(u_dict)

    pages = math.ceil(total / size) if total > 0 else 1
    return UserPagination(items=items, total=total, page=page, size=size, pages=pages)


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


from pydantic import BaseModel, Field

class ChangeRoleRequest(BaseModel):
    role: str = Field(..., description="New role code or name to assign to user")

@router.put("/{user_id}/role", summary="Change User Role (Admin Only)")
async def change_user_role(
    *,
    user_id: UUID,
    role_in: ChangeRoleRequest,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """
    Update target user's role.
    Strictly protected: ONLY Admin can call this endpoint.
    Non-admin callers receive HTTP 403 Forbidden.
    """
    valid_roles = ["Admin", "PI", "Researcher", "Bioinformatician", "QA", "Viewer", "Lab Technician"]
    target_role = role_in.role.strip()

    matching_role = next((r for r in valid_roles if r.lower() == target_role.lower()), None)
    if not matching_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{target_role}'. Allowed roles: {', '.join(valid_roles)}"
        )

    from app.models.identity import UserProfile, UserRole
    target_user = await User.find_one({"_id": user_id})
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    profile = await UserProfile.find_one({"user_id": user_id})
    if not profile:
        profile = UserProfile(user_id=user_id, designation=matching_role)
        await profile.insert()
    else:
        profile.designation = matching_role
        await profile.save()

    user_role = await UserRole.find_one({"user_id": user_id, "is_active": True})
    if not user_role:
        user_role = UserRole(user_id=user_id, role_name=matching_role, is_primary=True, is_active=True, assigned_by=current_user.id)
        await user_role.insert()
    else:
        user_role.role_name = matching_role
        user_role.assigned_by = current_user.id
        await user_role.save()

    is_self = (current_user.id == user_id)

    return {
        "message": f"Successfully updated role to {matching_role}",
        "user_id": str(user_id),
        "role": matching_role,
        "is_self": is_self
    }
