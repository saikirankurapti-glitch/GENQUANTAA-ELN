import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import refresh_token_repo
from app.models.identity import RefreshToken
from app.services.identity.exceptions import InvalidToken, TokenExpired

logger = logging.getLogger(__name__)

# Default Refresh token expiration: 7 days
DEFAULT_REFRESH_TOKEN_DAYS = 7


class RefreshTokenService:
    """Service governing refresh token issuance, rotation, and revocation."""

    def generate_token_pair(self) -> Tuple[str, str]:
        """Generate a raw refresh token string and SHA-256 hash."""
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return raw_token, token_hash

    async def issue_refresh_token(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        days_valid: int = DEFAULT_REFRESH_TOKEN_DAYS
    ) -> Tuple[RefreshToken, str]:
        """Issue a new refresh token for a user."""
        raw_token, token_hash = self.generate_token_pair()
        expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)

        token_obj = await refresh_token_repo.create(
            db,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
        )
        logger.info(f"RefreshTokenService: Issued refresh token {token_obj.id} for user {user_id}")
        return token_obj, raw_token

    async def rotate_refresh_token(
        self,
        db: AsyncSession,
        *,
        raw_refresh_token: str,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[RefreshToken, str]:
        """Rotate a refresh token (revoke the old token, issue a new token)."""
        token_hash = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()
        old_token = await refresh_token_repo.get_by_token_hash(db, token_hash=token_hash)
        if not old_token or old_token.revoked_at is not None:
            raise InvalidToken("Invalid or already revoked refresh token.")

        now = datetime.now(timezone.utc)
        if old_token.expires_at <= now:
            raise TokenExpired("Refresh token has expired.")

        # Revoke old token
        await refresh_token_repo.revoke_token(db, token_hash=token_hash)

        # Issue new token
        new_token_obj, new_raw_token = await self.issue_refresh_token(
            db,
            user_id=old_token.user_id,
            device_name=device_name or old_token.device_name,
            ip_address=ip_address or old_token.ip_address,
        )
        logger.info(f"RefreshTokenService: Rotated refresh token for user {old_token.user_id}")
        return new_token_obj, new_raw_token

    async def revoke_refresh_token(self, db: AsyncSession, *, raw_refresh_token: str) -> bool:
        """Revoke a refresh token."""
        token_hash = hashlib.sha256(raw_refresh_token.encode("utf-8")).hexdigest()
        return await refresh_token_repo.revoke_token(db, token_hash=token_hash)

    async def revoke_all_user_tokens(self, db: AsyncSession, *, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user."""
        return await refresh_token_repo.revoke_all_user_tokens(db, user_id=user_id)


refresh_token_service = RefreshTokenService()
