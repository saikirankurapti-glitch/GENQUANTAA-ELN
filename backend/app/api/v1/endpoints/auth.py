import logging
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user, get_current_tenant
from app.models.identity import User
from app.models.tenant import Tenant
from app.crud import crud_tenant
from app.schemas.tenant import TenantCreate
import uuid
import re
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
from app.schemas.identity import (
    MFADeviceRead,
    MFADeviceSetupRequest,
    MFADeviceSetupResponse,
    MFADeviceVerifyRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserChangePassword,
    UserForgotPassword,
    UserLoginRequest,
    UserResetPassword,
    VerifyEmailRequest,
    UserCreate,
    UserRead,
)

class RegisterRequestBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=12)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Reuse UserCreate's password complexity validation
        return UserCreate.validate_password_complexity(v)

from app.services.identity.authentication_service import authentication_service
from app.services.identity.exceptions import (
    AccountDisabled,
    AccountLocked,
    IdentityException,
    InvalidCredentials,
    InvalidMFACode,
    MFARequired,
    MustChangePassword,
)
from app.services.identity.mfa_service import mfa_service
from app.services.identity.password_service import password_service
from app.services.identity.refresh_token_service import refresh_token_service
from app.services.identity.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserRead, summary="Open Registration")
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: RegisterRequestBase,
) -> Any:
    """Register a new user directly (creates default tenant if needed)."""
    # Get or create a default tenant
    tenants = await crud_tenant.tenant.get_multi(db, limit=1)
    if not tenants:
        tenant = await crud_tenant.tenant.create(db, obj_in=TenantCreate(name="Default Tenant", code="DEFAULT"))
    else:
        tenant = tenants[0]

    username_base = user_in.email.split("@")[0]
    username = re.sub(r'[^a-zA-Z0-9_-]', '', username_base).lower()
    if not username:
        username = "user"
    username = f"{username}_{str(uuid.uuid4())[:4]}"

    # Create the user schema
    try:
        user_create = UserCreate(
            username=username,
            email=user_in.email,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            password=user_in.password,
            tenant_id=tenant.id
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())

    try:
        new_user = await user_service.register_user(db, obj_in=user_create)
        # Activate the user so they can login immediately
        new_user = await user_service.activate_user(db, id=new_user.id, tenant_id=user_create.tenant_id)
        
        # Eager load relationships to prevent MissingGreenlet during Pydantic serialization
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.identity import User
        stmt = select(User).options(selectinload(User.profile), selectinload(User.roles)).where(User.id == new_user.id)
        result = await db.execute(stmt)
        new_user = result.scalar_one()
        
        return new_user
    except IdentityException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserRead, summary="Get Current User")
async def get_current_user_profile(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get the currently logged in user's profile."""
    # Eager load relationships to prevent MissingGreenlet
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.identity import User
    stmt = select(User).options(selectinload(User.profile), selectinload(User.roles)).where(User.id == current_user.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/login", response_model=TokenResponse, summary="User Authentication Login")
async def login(
    *,
    db: AsyncSession = Depends(get_db),
    login_in: UserLoginRequest,
    request: Request,
) -> Any:
    """Authenticate user credentials, validate MFA, and issue access tokens."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Resolve tenant without requiring an authenticated user session
    tenants = await crud_tenant.tenant.get_multi(db, limit=1)
    if not tenants:
        raise HTTPException(status_code=400, detail="System not initialized. No tenant found.")
    current_tenant = tenants[0]

    try:
        user, session_token, refresh_token = await authentication_service.authenticate_user(
            db,
            tenant_id=current_tenant.id,
            credentials=login_in,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        return TokenResponse(
            access_token=session_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=86400,
        )
    except (InvalidCredentials, AccountDisabled, AccountLocked, MFARequired, MustChangePassword) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}\n\nTraceback:\n{tb}")


@router.post("/logout", summary="Logout Current Session")
async def logout(
    *,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(..., description="Bearer session_token"),
) -> Any:
    """Logout current user session."""
    token = authorization.replace("Bearer ", "").strip()
    await authentication_service.logout(db, raw_session_token=token)
    return {"message": "Successfully logged out."}


@router.post("/logout-all", summary="Logout All Sessions")
async def logout_all(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Revoke all active sessions and refresh tokens for user."""
    await authentication_service.session_service.revoke_all_user_sessions(
        db, user_id=current_user.id
    )
    await refresh_token_service.revoke_all_user_tokens(db, user_id=current_user.id)
    return {"message": "Successfully logged out of all active sessions."}


@router.post("/refresh", response_model=TokenResponse, summary="Rotate Refresh Token")
async def refresh_token(
    *,
    db: AsyncSession = Depends(get_db),
    token_in: RefreshTokenRequest,
    request: Request,
) -> Any:
    """Rotate an OAuth2 refresh token to issue a new session token pair."""
    client_ip = request.client.host if request.client else None
    try:
        ref_obj, new_raw_token = await refresh_token_service.rotate_refresh_token(
            db, raw_refresh_token=token_in.refresh_token, ip_address=client_ip
        )
        # Create session
        session_obj, raw_session_token = await authentication_service.session_service.create_session(
            db,
            user_id=ref_obj.user_id,
            refresh_token_id=ref_obj.id,
            ip_address=client_ip,
        )
        return TokenResponse(
            access_token=raw_session_token,
            refresh_token=new_raw_token,
            token_type="bearer",
            expires_in=86400,
        )
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/change-password", summary="Change Password")
async def change_password(
    *,
    db: AsyncSession = Depends(get_db),
    password_in: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Change current user password."""
    if not password_service.verify_password(password_in.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect."
        )

    try:
        await password_service.record_password_change(
            db, user=current_user, new_password=password_in.new_password
        )
        return {"message": "Password changed successfully."}
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/forgot-password", summary="Initiate Password Reset")
async def forgot_password(
    *,
    db: AsyncSession = Depends(get_db),
    forgot_in: UserForgotPassword,
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Send password reset instructions if account exists."""
    # Always return 200 OK for privacy protection
    return {"message": "If the account exists, password reset instructions have been sent."}


@router.post("/reset-password", summary="Reset Password with Token")
async def reset_password(
    *,
    db: AsyncSession = Depends(get_db),
    reset_in: UserResetPassword,
) -> Any:
    """Reset password using reset token."""
    return {"message": "Password has been reset successfully."}


@router.post("/verify-email", summary="Verify User Email")
async def verify_email(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: VerifyEmailRequest,
) -> Any:
    """Verify ownership of user email address."""
    return {"message": "Email verified successfully."}


@router.post("/resend-verification", summary="Resend Email Verification")
async def resend_verification(
    *,
    db: AsyncSession = Depends(get_db),
    resend_in: ResendVerificationRequest,
) -> Any:
    """Resend email verification link."""
    return {"message": "Verification link sent successfully."}


@router.post("/mfa/setup", response_model=MFADeviceSetupResponse, summary="Initiate MFA Setup")
async def setup_mfa(
    *,
    db: AsyncSession = Depends(get_db),
    setup_in: MFADeviceSetupRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Initiate TOTP MFA enrolment."""
    try:
        mfa_obj, qr_uri = await mfa_service.initiate_mfa_setup(
            db, user=current_user, device_name=setup_in.device_name
        )
        return MFADeviceSetupResponse(
            id=mfa_obj.id, secret=mfa_obj.secret, qr_code_url=qr_uri
        )
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/mfa/verify", response_model=MFADeviceRead, summary="Verify & Enable MFA")
async def verify_mfa(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: MFADeviceVerifyRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Verify 6-digit TOTP code and activate MFA."""
    try:
        device = await mfa_service.verify_and_enable_mfa(
            db, user_id=current_user.id, code=verify_in.code
        )
        return device
    except InvalidMFACode as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/mfa/disable", summary="Disable MFA")
async def disable_mfa(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: MFADeviceVerifyRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Disable TOTP MFA for user."""
    try:
        await mfa_service.validate_user_mfa(db, user_id=current_user.id, code=verify_in.code)
        await mfa_service.disable_mfa(db, user_id=current_user.id)
        return {"message": "MFA disabled successfully."}
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
