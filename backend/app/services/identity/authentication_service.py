import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import login_history_repo, user_repo, mfa_device_repo
from app.db.enums import UserStatus
from app.models.identity import User
from app.schemas.identity import UserLoginRequest
from app.services.identity.exceptions import (
    AccountDisabled,
    AccountLocked,
    InvalidCredentials,
    MFARequired,
    MustChangePassword,
    UserNotFound,
)
from app.services.identity.mfa_service import mfa_service
from app.services.identity.password_service import password_service
from app.services.identity.refresh_token_service import refresh_token_service
from app.services.identity.session_service import session_service

logger = logging.getLogger(__name__)

# Max failed login attempts before locking account
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


class AuthenticationService:
    """Master Authentication Service orchestrating login, brute-force checks, MFA, and sessions."""

    async def authenticate_user(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        credentials: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Authenticate user credentials, check lockout & MFA, issue tokens, create session, and record audit log.
        Returns (User, access_token_string, refresh_token_string).
        """
        identifier = credentials.username_or_email.lower().strip()

        # 1. Fetch user by username or email
        user = await user_repo.get_by_username(db, username=identifier, tenant_id=tenant_id)
        if not user:
            user = await user_repo.get_by_email(db, email=identifier, tenant_id=tenant_id)

        if not user:
            logger.warning(f"Authentication failure: User '{identifier}' not found in tenant {tenant_id}")
            raise InvalidCredentials("Invalid username/email or password.")

        # 2. Check if account is deleted or disabled
        if user.is_deleted or not user.is_active or user.status != UserStatus.ACTIVE:
            await login_history_repo.create(
                db,
                user_id=user.id,
                status="failed",
                ip_address=ip_address,
                device=credentials.device_name,
                failure_reason="Account disabled or suspended",
            )
            raise AccountDisabled("Account is disabled or suspended.")

        # 3. Check brute-force lockout status
        now = datetime.now(timezone.utc)
        if user.is_locked:
            if user.locked_until and user.locked_until > now:
                await login_history_repo.create(
                    db,
                    user_id=user.id,
                    status="failed",
                    ip_address=ip_address,
                    device=credentials.device_name,
                    failure_reason="Account locked due to consecutive failed attempts",
                )
                raise AccountLocked(
                    f"Account locked until {user.locked_until.strftime('%H:%M:%S UTC')} due to failed logins."
                )
            else:
                # Lockout window elapsed: automatically unlock
                await user_repo.update(
                    db, db_obj=user, obj_in={"is_locked": False, "failed_login_attempts": 0, "locked_until": None}
                )

        # 4. Verify password
        if not password_service.verify_password(credentials.password, user.password_hash):
            failed_attempts = user.failed_login_attempts + 1
            update_dict = {"failed_login_attempts": failed_attempts}

            if failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                update_dict["is_locked"] = True
                update_dict["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
                logger.warning(f"Account locked for user {user.id} after {failed_attempts} failed attempts.")

            await user_repo.update(db, db_obj=user, obj_in=update_dict)

            await login_history_repo.create(
                db,
                user_id=user.id,
                status="failed",
                ip_address=ip_address,
                device=credentials.device_name,
                failure_reason="Incorrect password",
            )
            raise InvalidCredentials("Invalid username/email or password.")

        # 5. Check MFA verification requirement if user has MFA setup
        mfa_devices = await mfa_device_repo.get_by_user_id(db, user_id=user.id)
        verified_mfa = [d for d in mfa_devices if d.verified]

        if verified_mfa:
            if not credentials.mfa_code:
                raise MFARequired("MFA code required to complete login.")
            await mfa_service.validate_user_mfa(db, user_id=user.id, code=credentials.mfa_code)

        # 6. Reset failed login attempt counter on successful login
        if user.failed_login_attempts > 0 or user.is_locked:
            await user_repo.update(
                db, db_obj=user, obj_in={"failed_login_attempts": 0, "is_locked": False, "locked_until": None}
            )

        # 7. Check if user is required to reset password
        if user.must_change_password:
            raise MustChangePassword("Password reset required prior to access.")

        # 8. Issue Refresh Token & JWT Access Token
        refresh_token_obj, raw_refresh_token = await refresh_token_service.issue_refresh_token(
            db, user_id=user.id, device_name=credentials.device_name, ip_address=ip_address
        )

        session_obj, raw_session_token = await session_service.create_session(
            db,
            user_id=user.id,
            refresh_token_id=refresh_token_obj.id,
            device_name=credentials.device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        from app.crud.crud_identity import user_profile_repo
        from app.core.security.jwt import create_access_token
        user_prof = await user_profile_repo.get_by_user_id(db, user_id=user.id)
        role = user_prof.designation if user_prof and user_prof.designation else "Researcher"
        jwt_access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            organization_id=str(user.organization_id) if user.organization_id else None,
            role=role,
            permissions=[],
        )

        # 9. Audit log success
        await login_history_repo.create(
            db,
            user_id=user.id,
            status="success",
            ip_address=ip_address,
            device=credentials.device_name,
        )

        logger.info(f"AuthenticationService: User '{user.username}' successfully authenticated.")
        return user, jwt_access_token, raw_refresh_token

    async def logout(self, db: AsyncSession, *, raw_session_token: str) -> bool:
        """Logout user by validating and revoking active session."""
        try:
            session = await session_service.validate_session(db, raw_session_token=raw_session_token)
            await session_service.revoke_session(db, session_id=session.id)
            if session.refresh_token_id:
                ref_token = await refresh_token_service.refresh_token_repo.get_by_id(
                    db, id=session.refresh_token_id
                )
                if ref_token:
                    await refresh_token_service.revoke_refresh_token(
                        db, raw_refresh_token=ref_token.token_hash
                    )
            logger.info(f"AuthenticationService: User {session.user_id} logged out.")
            return True
        except Exception as e:
            logger.warning(f"Logout warning: {e}")
            return False


authentication_service = AuthenticationService()
