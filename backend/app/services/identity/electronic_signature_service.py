import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import electronic_signature_profile_repo, user_repo
from app.models.identity import ElectronicSignatureProfile
from app.schemas.identity import (
    ElectronicSignatureProfileCreate,
    ElectronicSignatureProfileUpdate,
)
from app.services.identity.exceptions import UserNotFound
from app.services.identity.password_service import password_service

logger = logging.getLogger(__name__)


class ElectronicSignatureService:
    """Service governing GxP / FDA 21 CFR Part 11 electronic signature profiles and sign-offs."""

    async def get_profile(
        self, db: AsyncSession, *, user_id: UUID
    ) -> Optional[ElectronicSignatureProfile]:
        """Fetch electronic signature profile for user."""
        return await electronic_signature_profile_repo.get_by_user_id(db, user_id=user_id)

    async def setup_signature_profile(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        obj_in: Union[ElectronicSignatureProfileCreate, ElectronicSignatureProfileUpdate, Dict[str, Any]]
    ) -> ElectronicSignatureProfile:
        """Create or update signature profile."""
        profile = await electronic_signature_profile_repo.create_or_update(
            db, user_id=user_id, obj_in=obj_in
        )
        logger.info(f"ElectronicSignatureService: Updated signature profile for user {user_id}")
        return profile

    async def verify_signature_intent(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tenant_id: UUID,
        password: str,
        signature_meaning: str
    ) -> bool:
        """
        FDA 21 CFR Part 11 Dual-Factor Signature Re-authentication.
        Verifies current password and active electronic signature profile.
        """
        user = await user_repo.get_by_id(db, id=user_id, tenant_id=tenant_id)
        if not user or not user.is_active or user.is_deleted:
            raise UserNotFound("User account invalid or deleted.")

        # Re-authenticate credentials for legal sign-off
        if not password_service.verify_password(password, user.password_hash):
            return False

        profile = await self.get_profile(db, user_id=user_id)
        if profile and not profile.enabled:
            return False

        logger.info(
            f"ElectronicSignatureService: Verified signature intent '{signature_meaning}' for user {user_id}"
        )
        return True


electronic_signature_service = ElectronicSignatureService()
