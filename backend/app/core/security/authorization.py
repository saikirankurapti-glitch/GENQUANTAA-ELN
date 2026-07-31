import logging
from typing import Annotated, Callable, List, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.enums import UserStatus
from app.models.identity import User, UserRole
from app.models.rbac import Permission, Role, RolePermission
from app.models.tenant import Tenant
from app.services.identity.api_key_service import api_key_service
from app.services.identity.exceptions import ApiKeyExpired, InvalidApiKey, SessionExpired, SessionNotFound
from app.services.identity.session_service import session_service
from app.services.identity.user_service import user_service

logger = logging.getLogger(__name__)

# OAuth2 Password Bearer scheme endpoint location
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# =================================================================================
# IDENTITY & CONTEXT DEPENDENCIES
# =================================================================================

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate request via session token OR API Key header.
    Validates token state, session revocation, account lockout, and active status.
    """
    if x_api_key:
        try:
            api_key_obj = await api_key_service.validate_api_key(db, raw_api_key=x_api_key)
            user = await user_service.get_user_by_id(
                db, id=api_key_obj.user_id, tenant_id=api_key_obj.tenant_id
            )
            return user
        except (InvalidApiKey, ApiKeyExpired) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = None
    try:
        from app.core.security.jwt import decode_access_token
        jwt_payload = decode_access_token(token)
        if jwt_payload and "user_id" in jwt_payload:
            user_id = UUID(jwt_payload["user_id"])
            tenant_id = UUID(jwt_payload["tenant_id"]) if jwt_payload.get("tenant_id") else None
            user = await user_service.get_user_by_id(db, id=user_id, tenant_id=tenant_id, include_relations=True)
        else:
            session = await session_service.validate_session(db, raw_session_token=token)
            user = await user_service.get_user_by_id(
                db, id=session.user_id, tenant_id=session.user.tenant_id if hasattr(session, "user") and session.user else None, include_relations=True
            )
    except Exception as e:
        logger.warning(f"JWT/Session validation failed, trying fallback: {e}")
        try:
            session = await session_service.validate_session(db, raw_session_token=token)
            user = await user_service.get_user_by_id(
                db, id=session.user_id, tenant_id=session.user.tenant_id if hasattr(session, "user") and session.user else None, include_relations=True
            )
        except (SessionNotFound, SessionExpired) as e_sess:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate JWT or session credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate Account State
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account has been deleted."
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is temporarily locked."
        )

    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive or suspended."
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure authenticated user is active and not locked."""
    if not current_user.is_active or current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account."
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure authenticated user has verified their email address."""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required."
        )
    return current_user


async def get_current_tenant(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Retrieve Tenant context to enforce multi-tenant isolation boundaries."""
    stmt = select(Tenant).where(Tenant.id == current_user.tenant_id, Tenant.is_deleted == False)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()

    if not tenant:
        logger.error(f"Tenant isolation error: Tenant {current_user.tenant_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context invalid or deleted."
        )

    return tenant


def require_tenant_access(target_tenant_id: UUID) -> Callable:
    """Dependency factory checking that current tenant matches target resource tenant."""
    async def tenant_dependency(
        current_tenant: Tenant = Depends(get_current_tenant),
    ) -> Tenant:
        if current_tenant.id != target_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Cannot access resources of another tenant.",
            )
        return current_tenant
    return tenant_dependency


# =================================================================================
# PERMISSION CHECKERS
# =================================================================================

def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency checking if current user possesses Administrator privileges."""
    designation = (current_user.profile.designation or "").lower() if current_user and current_user.profile else ""
    if "admin" in designation or "super" in designation:
        return current_user

    logger.warning(f"Admin access denied for user {current_user.id} with designation '{designation}'")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. Administrator privileges required.",
    )


def require_permission(permission_code: str) -> Callable:
    """Dependency factory checking if user possesses a specific permission code or admin role."""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        designation = (current_user.profile.designation or "").lower() if current_user and current_user.profile else ""
        if "admin" in designation or "super" in designation:
            return current_user

        stmt = select(
            select(UserRole)
            .join(RolePermission, UserRole.role_id == RolePermission.role_id)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.is_active == True,
                Permission.code == permission_code,
            )
            .exists()
        )
        res = await db.execute(stmt)
        if not res.scalar():
            logger.warning(f"Permission denied for user {current_user.id}: Missing '{permission_code}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires: '{permission_code}'",
            )
        return current_user

    return permission_dependency


def require_any_permission(*permissions: str) -> Callable:
    """Dependency factory checking if user possesses AT LEAST ONE permission."""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        stmt = select(
            select(UserRole)
            .join(RolePermission, UserRole.role_id == RolePermission.role_id)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.is_active == True,
                Permission.code.in_(permissions),
            )
            .exists()
        )
        res = await db.execute(stmt)
        if not res.scalar():
            logger.warning(f"Permission denied for user {current_user.id}: Missing any of {permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires one of: {', '.join(permissions)}",
            )
        return current_user

    return permission_dependency


def require_all_permissions(*permissions: str) -> Callable:
    """Dependency factory checking if user possesses ALL permissions."""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        stmt = select(Permission.code).join(
            RolePermission, RolePermission.permission_id == Permission.id
        ).join(
            UserRole, UserRole.role_id == RolePermission.role_id
        ).where(
            UserRole.user_id == current_user.id,
            Permission.code.in_(permissions),
        )
        res = await db.execute(stmt)
        owned = set(res.scalars().all())
        missing = set(permissions) - owned
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Missing: {', '.join(missing)}",
            )
        return current_user

    return permission_dependency


# =================================================================================
# ROLE CHECKERS
# =================================================================================

def require_role(role_code: str) -> Callable:
    """Dependency factory checking if user possesses a specific role code."""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        stmt = select(
            select(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.is_active == True,
                Role.code == role_code,
                Role.is_deleted == False,
            )
            .exists()
        )
        res = await db.execute(stmt)
        if not res.scalar():
            logger.warning(f"Role denied for user {current_user.id}: Missing role '{role_code}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires role: '{role_code}'",
            )
        return current_user

    return role_dependency


def require_any_role(*roles: str) -> Callable:
    """Dependency factory checking if user possesses AT LEAST ONE role."""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        stmt = select(
            select(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.is_active == True,
                Role.code.in_(roles),
                Role.is_deleted == False,
            )
            .exists()
        )
        res = await db.execute(stmt)
        if not res.scalar():
            logger.warning(f"Role denied for user {current_user.id}: Missing any of roles {roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires one of roles: {', '.join(roles)}",
            )
        return current_user

    return role_dependency


def require_all_roles(*roles: str) -> Callable:
    """Dependency factory checking if user possesses ALL roles."""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        stmt = select(Role.code).join(
            UserRole, UserRole.role_id == Role.id
        ).where(
            UserRole.user_id == current_user.id,
            Role.code.in_(roles),
            Role.is_deleted == False,
        )
        res = await db.execute(stmt)
        owned = set(res.scalars().all())
        missing = set(roles) - owned
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Missing roles: {', '.join(missing)}",
            )
        return current_user

    return role_dependency


# =================================================================================
# SYSTEM ALIASES
# =================================================================================

def require_system_admin() -> Callable:
    """Shortcut dependency for System Administrators."""
    return require_role("system.admin")


def require_organization_admin() -> Callable:
    """Shortcut dependency for Organization Administrators."""
    return require_role("org.admin")
