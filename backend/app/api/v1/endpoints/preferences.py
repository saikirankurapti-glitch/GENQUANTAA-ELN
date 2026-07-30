import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user
from app.models.identity import User
from app.schemas.identity import UserPreferenceRead, UserPreferenceUpdate
from app.services.identity.user_preference_service import user_preference_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserPreferenceRead, summary="Get User Preferences")
async def get_my_preferences(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get UI/UX preferences for current user."""
    return await user_preference_service.get_user_preferences(db, user_id=current_user.id)


@router.put("/me", response_model=UserPreferenceRead, summary="Update User Preferences")
async def update_my_preferences(
    *,
    db: AsyncSession = Depends(get_db),
    pref_in: UserPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update UI/UX preferences for current user."""
    return await user_preference_service.update_user_preferences(
        db, user_id=current_user.id, obj_in=pref_in
    )
