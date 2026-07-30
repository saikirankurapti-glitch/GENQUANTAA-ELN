import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import api_key_repo
from app.models.identity import ApiKey
from app.services.identity.exceptions import (
    ApiKeyExpired,
    ApiKeyNotFound,
    InvalidApiKey,
)

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "eln_ak_"


class ApiKeyService:
    """Service governing API Key creation, prefix hashing, verification, and revocation."""

    def generate_api_key(self) -> Tuple[str, str]:
        """Generate a raw API key (eln_ak_...) and its SHA-256 hash string."""
        raw_token = secrets.token_urlsafe(36)
        raw_key = f"{API_KEY_PREFIX}{raw_token}"
        hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return raw_key, hashed_key

    async def create_api_key(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        expires_at: Optional[datetime] = None
    ) -> Tuple[ApiKey, str]:
        """Create an API key, returning the DB record and raw secret key string (exposed ONCE)."""
        raw_key, hashed_key = self.generate_api_key()
        api_key_obj = await api_key_repo.create(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            hashed_key=hashed_key,
            expires_at=expires_at,
        )
        logger.info(f"ApiKeyService: Created API Key '{name}' for user {user_id}")
        return api_key_obj, raw_key

    async def validate_api_key(self, db: AsyncSession, *, raw_api_key: str) -> ApiKey:
        """Validate an incoming raw API key string against stored hashes."""
        if not raw_api_key.startswith(API_KEY_PREFIX):
            raise InvalidApiKey("Invalid API key format prefix.")

        hashed_key = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        api_key_obj = await api_key_repo.get_by_hashed_key(db, hashed_key=hashed_key)
        if not api_key_obj or not api_key_obj.is_active:
            raise InvalidApiKey("API key is invalid or deactivated.")

        if api_key_obj.expires_at and api_key_obj.expires_at <= datetime.now(timezone.utc):
            raise ApiKeyExpired("API key has expired.")

        # Update last used timestamp
        await api_key_repo.update_last_used(db, id=api_key_obj.id)
        return api_key_obj

    async def revoke_api_key(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> bool:
        """Deactivate an API Key."""
        api_key_obj = await api_key_repo.get_by_id(db, id=id, tenant_id=tenant_id)
        if not api_key_obj:
            raise ApiKeyNotFound(f"API key {id} not found.")

        return await api_key_repo.deactivate(db, id=id)

    async def list_user_api_keys(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID
    ) -> List[ApiKey]:
        """List all API keys for user."""
        return await api_key_repo.get_by_user_id(db, user_id=user_id, tenant_id=tenant_id)


api_key_service = ApiKeyService()
