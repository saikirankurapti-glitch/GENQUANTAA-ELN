import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import trusted_device_repo
from app.models.identity import TrustedDevice

logger = logging.getLogger(__name__)


class TrustedDeviceService:
    """Service governing trusted device registration and verification."""

    async def register_trusted_device(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        device_identifier: str,
        device_name: Optional[str] = None,
        browser: Optional[str] = None,
        operating_system: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> TrustedDevice:
        """Register or update a trusted device."""
        existing = await trusted_device_repo.get_by_device_identifier(
            db, user_id=user_id, device_identifier=device_identifier
        )
        if existing:
            await trusted_device_repo.update_last_seen(db, id=existing.id)
            return existing

        device = await trusted_device_repo.create(
            db,
            user_id=user_id,
            device_identifier=device_identifier,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
        )
        logger.info(f"TrustedDeviceService: Registered device {device_identifier} for user {user_id}")
        return device

    async def is_device_trusted(
        self, db: AsyncSession, *, user_id: UUID, device_identifier: str
    ) -> bool:
        """Check if device fingerprint is registered as trusted."""
        device = await trusted_device_repo.get_by_device_identifier(
            db, user_id=user_id, device_identifier=device_identifier
        )
        if device:
            await trusted_device_repo.update_last_seen(db, id=device.id)
            return True
        return False

    async def list_trusted_devices(
        self, db: AsyncSession, *, user_id: UUID
    ) -> List[TrustedDevice]:
        """List all trusted devices for user."""
        return await trusted_device_repo.get_by_user_id(db, user_id=user_id)


trusted_device_service = TrustedDeviceService()
