import hashlib
import hmac
import logging
import re
import secrets
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import password_history_repo, user_repo
from app.models.identity import User
from app.services.identity.exceptions import (
    PasswordPolicyError,
    PasswordReuseError,
    UserNotFound,
)

logger = logging.getLogger(__name__)

# Security parameters
SALT_SIZE = 16
HASH_ITERATIONS = 100_000


class PasswordService:
    """Service governing password hashing, verification, history, and policy rules."""

    def hash_password(self, password: str) -> str:
        """Cryptographically hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
        salt = secrets.token_hex(SALT_SIZE)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), HASH_ITERATIONS
        ).hex()
        return f"pbkdf2_sha256${HASH_ITERATIONS}${salt}${pwd_hash}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against its stored hash format."""
        try:
            parts = hashed_password.split("$")
            if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
                return False
            iterations = int(parts[1])
            salt = parts[2]
            stored_hash = parts[3]

            computed_hash = hashlib.pbkdf2_hmac(
                "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations
            ).hex()

            return hmac.compare_digest(stored_hash, computed_hash)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def validate_complexity(self, password: str) -> None:
        """Enforce enterprise password complexity policy."""
        if len(password) < 12:
            raise PasswordPolicyError("Password must be at least 12 characters long.")
        if not re.search(r"[A-Z]", password):
            raise PasswordPolicyError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise PasswordPolicyError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            raise PasswordPolicyError("Password must contain at least one numeric digit.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
            raise PasswordPolicyError("Password must contain at least one special character.")

    async def check_password_history(
        self, db: AsyncSession, *, user_id: UUID, new_password: str, history_limit: int = 5
    ) -> None:
        """Prevent password re-use against the last N recorded password hashes."""
        recent_histories = await password_history_repo.get_recent_by_user(
            db, user_id=user_id, limit=history_limit
        )
        for history in recent_histories:
            if self.verify_password(new_password, history.password_hash):
                raise PasswordReuseError(
                    f"Password cannot be one of your last {history_limit} passwords used."
                )

    async def record_password_change(
        self, db: AsyncSession, *, user: User, new_password: str
    ) -> None:
        """Validate, hash, update user password, and append to password history."""
        self.validate_complexity(new_password)
        await self.check_password_history(db, user_id=user.id, new_password=new_password)

        new_hash = self.hash_password(new_password)

        # Record history prior to updating current
        await password_history_repo.create(db, user_id=user.id, password_hash=user.password_hash)

        # Update user
        await user_repo.update(
            db,
            db_obj=user,
            obj_in={
                "password_hash": new_hash,
                "password_changed_at": user.updated_at,
                "must_change_password": False,
                "failed_login_attempts": 0,
                "is_locked": False,
                "locked_until": None,
            },
        )
        logger.info(f"PasswordService: Successfully changed password for user {user.id}")


password_service = PasswordService()
