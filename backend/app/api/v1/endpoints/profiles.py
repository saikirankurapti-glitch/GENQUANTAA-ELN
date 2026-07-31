import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.identity import UserProfileRead, UserProfileUpdate
from app.services.identity.exceptions import UserNotFound
from app.services.identity.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserProfileRead, summary="Get Current Profile")
async def get_my_profile(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch profile details for currently logged-in user."""
    user = await user_service.get_user_by_id(
        db, id=current_user.id, tenant_id=current_tenant.id, include_relations=True
    )
    if not user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not configured yet."
        )
    return user.profile


@router.put("/me", response_model=UserProfileRead, summary="Update Current Profile")
async def update_my_profile(
    *,
    db: AsyncSession = Depends(get_db),
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Update profile details for currently logged-in user."""
    from app.crud.crud_identity import user_profile_repo
    await user_service.update_profile(
        db, user_id=current_user.id, tenant_id=current_tenant.id, obj_in=profile_in
    )
    profile = await user_profile_repo.get_by_user_id(db, user_id=current_user.id)
    return profile


@router.get("/{user_id}", response_model=UserProfileRead, summary="Get User Profile by ID")
async def get_user_profile(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_permission("identity.user.read")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch user profile by target user ID."""
    try:
        user = await user_service.get_user_by_id(
            db, id=user_id, tenant_id=current_tenant.id, include_relations=True
        )
        if not user.profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not configured."
            )
        return user.profile
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}", response_model=UserProfileRead, summary="Update User Profile by ID")
async def update_user_profile(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    profile_in: UserProfileUpdate,
    current_user: User = Depends(require_permission("identity.user.update")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Update user profile by target user ID."""
    try:
        updated_user = await user_service.update_profile(
            db, user_id=user_id, tenant_id=current_tenant.id, obj_in=profile_in
        )
        return updated_user.profile
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
