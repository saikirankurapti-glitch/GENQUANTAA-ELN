import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import user_session_repo
from app.models.identity import UserSession
from app.services.identity.exceptions import SessionExpired, SessionNotFound

logger = logging.getLogger(__name__)

# Default session duration: 24 hours
DEFAULT_SESSION_HOURS = 24


class SessionService:
    """Service governing active user sessions, device tracking, and revocations."""

    def generate_session_token(self) -> Tuple[str, str]:
        """Generate a raw session token and its SHA-256 hash for secure storage."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return raw_token, token_hash

    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        refresh_token_id: Optional[UUID] = None,
        device_name: Optional[str] = None,
        browser: Optional[str] = None,
        operating_system: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_hours: int = DEFAULT_SESSION_HOURS
    ) -> Tuple[UserSession, str]:
        """Create a new session, returning the session model and raw token string."""
        raw_token, token_hash = self.generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=session_hours)

        session = await user_session_repo.create(
            db,
            user_id=user_id,
            session_token_hash=token_hash,
            refresh_token_id=refresh_token_id,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        logger.info(f"SessionService: Created session {session.id} for user {user_id}")
        return session, raw_token

    async def validate_session(self, db: AsyncSession, *, raw_session_token: str) -> UserSession:
        """Validate an active session token string."""
        token_hash = hashlib.sha256(raw_session_token.encode("utf-8")).hexdigest()
        session = await user_session_repo.get_by_session_token_hash(db, session_token_hash=token_hash)
        if not session or session.is_revoked:
            raise SessionNotFound("Session not found or revoked.")

        now = datetime.now(timezone.utc)
        if session.expires_at <= now:
            raise SessionExpired("Session has expired.")

        # Update last activity
        await user_session_repo.update_last_activity(db, session_id=session.id)
        return session

    async def revoke_session(self, db: AsyncSession, *, session_id: UUID) -> bool:
        """Revoke a specific user session."""
        return await user_session_repo.revoke_session(db, session_id=session_id)

    async def revoke_all_user_sessions(
        self, db: AsyncSession, *, user_id: UUID, except_session_id: Optional[UUID] = None
    ) -> int:
        """Revoke all sessions for a user."""
        return await user_session_repo.revoke_all_user_sessions(
            db, user_id=user_id, except_session_id=except_session_id
        )

    async def list_active_sessions(
        self, db: AsyncSession, *, user_id: UUID
    ) -> List[UserSession]:
        """Fetch all active sessions for a user."""
        return await user_session_repo.get_active_sessions_by_user(db, user_id=user_id)


session_service = SessionService()
