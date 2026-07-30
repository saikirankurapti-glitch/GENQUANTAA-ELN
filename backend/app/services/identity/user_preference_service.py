import logging
from typing import Any, Dict, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import user_preference_repo
from app.models.identity import UserPreference
from app.schemas.identity import UserPreferenceUpdate

logger = logging.getLogger(__name__)


class UserPreferenceService:
    """Service governing UI settings and notification preferences."""

    async def get_user_preferences(
        self, db: AsyncSession, *, user_id: UUID
    ) -> UserPreference:
        """Fetch user preferences, creating defaults if not existing."""
        pref = await user_preference_repo.get_by_user_id(db, user_id=user_id)
        if not pref:
            pref = await user_preference_repo.create_or_update(
                db, user_id=user_id, obj_in={"theme": "light", "language": "en", "time_zone": "UTC"}
            )
        return pref

    async def update_user_preferences(
        self, db: AsyncSession, *, user_id: UUID, obj_in: Union[UserPreferenceUpdate, Dict[str, Any]]
    ) -> UserPreference:
        """Update user preferences."""
        return await user_preference_repo.create_or_update(db, user_id=user_id, obj_in=obj_in)


user_preference_service = UserPreferenceService()
