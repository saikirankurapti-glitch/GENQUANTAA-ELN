import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.identity import (
    ApiKey,
    ElectronicSignatureProfile,
    LoginHistory,
    MFADevice,
    PasswordHistory,
    RefreshToken,
    TrustedDevice,
    User,
    UserProfile,
    UserPreference,
    UserRole,
    UserSession,
)
from app.schemas.identity import (
    ApiKeyCreate,
    ElectronicSignatureProfileCreate,
    ElectronicSignatureProfileUpdate,
    UserProfileCreate,
    UserProfileUpdate,
    UserPreferenceUpdate,
    UserRoleCreate,
    UserRoleUpdate,
    UserCreate,
    UserUpdate,
)

logger = logging.getLogger(__name__)


# ==========================================
# 1. User Repository
# ==========================================

class UserRepository:
    """Data Access Layer for User model with tenant isolation and eager loading."""

    async def create(self, db: AsyncSession, *, obj_in: UserCreate, password_hash: str) -> User:
        """Create a new user with password hash."""
        user_data = obj_in.model_dump(exclude={"password", "profile"})
        user_data["password_hash"] = password_hash
        
        db_user = User(**user_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # Create profile if provided in payload
        if obj_in.profile:
            profile_data = obj_in.profile.model_dump()
            db_profile = UserProfile(user_id=db_user.id, **profile_data)
            db.add(db_profile)
            await db.commit()
            await db.refresh(db_user)

        logger.info(f"Created User '{db_user.username}' for Tenant '{db_user.tenant_id}'")
        return db_user

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: Optional[UUID] = None,
        include_relations: bool = False
    ) -> Optional[User]:
        """Fetch User by ID, excluding soft deleted records."""
        stmt = select(User).where(User.id == id, User.is_deleted == False)
        if tenant_id:
            stmt = stmt.where(User.tenant_id == tenant_id)

        if include_relations:
            stmt = stmt.options(
                selectinload(User.profile),
                selectinload(User.roles).selectinload(UserRole.role),
                selectinload(User.preference),
                selectinload(User.signature_profile),
            )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(
        self, db: AsyncSession, *, username: str, tenant_id: UUID
    ) -> Optional[User]:
        """Fetch User by username within tenant scope."""
        stmt = select(User).where(
            User.username == username.lower().strip(),
            User.tenant_id == tenant_id,
            User.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self, db: AsyncSession, *, email: str, tenant_id: UUID
    ) -> Optional[User]:
        """Fetch User by email within tenant scope."""
        stmt = select(User).where(
            User.email == email.lower().strip(),
            User.tenant_id == tenant_id,
            User.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_employee_id(
        self, db: AsyncSession, *, employee_id: str, tenant_id: UUID
    ) -> Optional[User]:
        """Fetch User by corporate employee ID."""
        stmt = select(User).where(
            User.employee_id == employee_id,
            User.tenant_id == tenant_id,
            User.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_username(self, db: AsyncSession, *, username: str, tenant_id: UUID) -> bool:
        """Check if username exists for tenant."""
        stmt = select(
            select(User)
            .where(
                User.username == username.lower().strip(),
                User.tenant_id == tenant_id,
                User.is_deleted == False,
            )
            .exists()
        )
        result = await db.execute(stmt)
        return bool(result.scalar())

    async def exists_by_email(self, db: AsyncSession, *, email: str, tenant_id: UUID) -> bool:
        """Check if email exists for tenant."""
        stmt = select(
            select(User)
            .where(
                User.email == email.lower().strip(),
                User.tenant_id == tenant_id,
                User.is_deleted == False,
            )
            .exists()
        )
        result = await db.execute(stmt)
        return bool(result.scalar())

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update User attributes."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Updated User {db_obj.id}")
        return db_obj

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, deleted_by: Optional[UUID] = None
    ) -> Optional[User]:
        """Soft delete User account (GxP / Part 11 compliant)."""
        user = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if user:
            user.is_deleted = True
            user.deleted_at = datetime.now(timezone.utc)
            user.deleted_by = deleted_by
            user.is_active = False
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Soft deleted User {id} for tenant {tenant_id}")
        return user

    async def restore(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID
    ) -> Optional[User]:
        """Restore soft deleted User account."""
        stmt = select(User).where(User.id == id, User.tenant_id == tenant_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.is_deleted:
            user.is_deleted = False
            user.deleted_at = None
            user.deleted_by = None
            user.is_active = True
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Restored User {id}")
        return user

    async def hard_delete(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> bool:
        """Hard delete User record (Only when explicitly allowed by admin)."""
        user = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if user:
            await db.delete(user)
            await db.commit()
            logger.warning(f"Hard deleted User {id}")
            return True
        return False

    async def search(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        query: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_locked: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[User], int]:
        """Search & filter users with pagination."""
        stmt = select(User).where(User.tenant_id == tenant_id, User.is_deleted == False)

        if organization_id:
            stmt = stmt.where(User.organization_id == organization_id)
        if status:
            stmt = stmt.where(User.status == status)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if is_locked is not None:
            stmt = stmt.where(User.is_locked == is_locked)

        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.employee_id.ilike(search_term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        # Sorting
        sort_attr = getattr(User, sort_by, User.created_at)
        stmt = stmt.order_by(sort_attr.desc() if sort_order.lower() == "desc" else sort_attr.asc())

        # Pagination & Eager loading
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size).options(
            selectinload(User.profile),
            selectinload(User.roles).selectinload(UserRole.role)
        )

        res = await db.execute(stmt)
        return list(res.scalars().all()), total


# ==========================================
# 2. User Profile Repository
# ==========================================

class UserProfileRepository:
    """Data Access Layer for UserProfile model."""

    async def create(
        self, db: AsyncSession, *, obj_in: Union[UserProfileCreate, UserProfileUpdate, Dict[str, Any]], user_id: UUID
    ) -> UserProfile:
        """Create a new user profile."""
        profile_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        profile = UserProfile(user_id=user_id, **profile_data)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[UserProfile]:
        """Fetch profile by ID."""
        stmt = select(UserProfile).where(UserProfile.id == id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, *, user_id: UUID) -> Optional[UserProfile]:
        """Fetch profile by associated User ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self, db: AsyncSession, *, db_obj: UserProfile, obj_in: Union[UserProfileUpdate, Dict[str, Any]]
    ) -> UserProfile:
        """Update profile details."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, val)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# ==========================================
# 3. User Role Repository
# ==========================================

class UserRoleRepository:
    """Data Access Layer for UserRole association model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID,
        assigned_by: Optional[UUID] = None,
        is_primary: bool = False,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """Assign role to user."""
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            is_primary=is_primary,
            expires_at=expires_at,
        )
        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)
        return user_role

    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[UserRole]:
        """Fetch UserRole mapping by ID."""
        stmt = select(UserRole).where(UserRole.id == id).options(joinedload(UserRole.role))
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_and_role(
        self, db: AsyncSession, *, user_id: UUID, role_id: UUID
    ) -> Optional[UserRole]:
        """Fetch explicit UserRole mapping by user and role pair."""
        stmt = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, *, user_id: UUID) -> List[UserRole]:
        """Fetch all role assignments for a user."""
        stmt = (
            select(UserRole)
            .where(UserRole.user_id == user_id, UserRole.is_active == True)
            .options(joinedload(UserRole.role))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def hard_delete(self, db: AsyncSession, *, user_id: UUID, role_id: UUID) -> bool:
        """Revoke role assignment."""
        mapping = await self.get_by_user_and_role(db, user_id=user_id, role_id=role_id)
        if mapping:
            await db.delete(mapping)
            await db.commit()
            return True
        return False


# ==========================================
# 4. User Session Repository
# ==========================================

class UserSessionRepository:
    """Data Access Layer for UserSession model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        session_token_hash: str,
        refresh_token_id: Optional[UUID] = None,
        device_name: Optional[str] = None,
        browser: Optional[str] = None,
        operating_system: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_at: datetime
    ) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            user_id=user_id,
            session_token_hash=session_token_hash,
            refresh_token_id=refresh_token_id,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[UserSession]:
        """Get session by ID."""
        stmt = select(UserSession).where(UserSession.id == id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_session_token_hash(
        self, db: AsyncSession, *, session_token_hash: str
    ) -> Optional[UserSession]:
        """Fetch session by session token hash."""
        stmt = select(UserSession).where(
            UserSession.session_token_hash == session_token_hash,
            UserSession.is_revoked == False
        ).options(selectinload(UserSession.user))
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_sessions_by_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> List[UserSession]:
        """Get all active sessions for a user."""
        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,
            UserSession.expires_at > now
        ).order_by(UserSession.last_activity.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_last_activity(self, db: AsyncSession, *, session_id: UUID) -> None:
        """Touch session timestamp on user interaction."""
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(last_activity=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()

    async def revoke_session(self, db: AsyncSession, *, session_id: UUID) -> bool:
        """Revoke specific session."""
        session = await self.get_by_id(db, id=session_id)
        if session:
            session.is_revoked = True
            db.add(session)
            await db.commit()
            return True
        return False

    async def revoke_all_user_sessions(
        self, db: AsyncSession, *, user_id: UUID, except_session_id: Optional[UUID] = None
    ) -> int:
        """Revoke all active sessions for user (e.g. on logout-all or security alert)."""
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_revoked == False)
        )
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)

        stmt = stmt.values(is_revoked=True)
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount


# ==========================================
# 5. Refresh Token Repository
# ==========================================

class RefreshTokenRepository:
    """Data Access Layer for RefreshToken model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> RefreshToken:
        """Create refresh token record."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    async def get_by_token_hash(
        self, db: AsyncSession, *, token_hash: str
    ) -> Optional[RefreshToken]:
        """Fetch token by token hash."""
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke_token(self, db: AsyncSession, *, token_hash: str) -> bool:
        """Revoke token."""
        token = await self.get_by_token_hash(db, token_hash=token_hash)
        if token:
            token.revoked_at = datetime.now(timezone.utc)
            db.add(token)
            await db.commit()
            return True
        return False

    async def revoke_all_user_tokens(self, db: AsyncSession, *, user_id: UUID) -> int:
        """Revoke all active refresh tokens for user."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount


# ==========================================
# 6. Password History Repository
# ==========================================

class PasswordHistoryRepository:
    """Data Access Layer for PasswordHistory model."""

    async def create(self, db: AsyncSession, *, user_id: UUID, password_hash: str) -> PasswordHistory:
        """Log old password hash."""
        history = PasswordHistory(user_id=user_id, password_hash=password_hash)
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history

    async def get_recent_by_user(
        self, db: AsyncSession, *, user_id: UUID, limit: int = 5
    ) -> List[PasswordHistory]:
        """Fetch recent N password hashes for non-reuse checks."""
        stmt = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.changed_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


# ==========================================
# 7. Login History Repository
# ==========================================

class LoginHistoryRepository:
    """Data Access Layer for LoginHistory model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        status: str,
        ip_address: Optional[str] = None,
        device: Optional[str] = None,
        browser: Optional[str] = None,
        operating_system: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> LoginHistory:
        """Record login audit entry."""
        history = LoginHistory(
            user_id=user_id,
            status=status,
            ip_address=ip_address,
            device=device,
            browser=browser,
            operating_system=operating_system,
            country=country,
            city=city,
            failure_reason=failure_reason,
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: UUID, page: int = 1, page_size: int = 50
    ) -> Tuple[List[LoginHistory], int]:
        """Fetch login logs for user with pagination."""
        stmt = select(LoginHistory).where(LoginHistory.user_id == user_id)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        skip = (page - 1) * page_size
        stmt = stmt.order_by(LoginHistory.login_time.desc()).offset(skip).limit(page_size)

        res = await db.execute(stmt)
        return list(res.scalars().all()), total


# ==========================================
# 8. MFA Device Repository
# ==========================================

class MFADeviceRepository:
    """Data Access Layer for MFADevice model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        secret: str,
        device_name: str = "Primary MFA Device",
        type: str = "totp"
    ) -> MFADevice:
        """Setup new MFA device."""
        device = MFADevice(user_id=user_id, secret=secret, device_name=device_name, type=type)
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device

    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[MFADevice]:
        """Fetch MFA device by ID."""
        stmt = select(MFADevice).where(MFADevice.id == id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, *, user_id: UUID) -> List[MFADevice]:
        """Fetch all MFA devices for user."""
        stmt = select(MFADevice).where(MFADevice.user_id == user_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def verify_device(self, db: AsyncSession, *, id: UUID) -> Optional[MFADevice]:
        """Mark MFA device verified."""
        device = await self.get_by_id(db, id=id)
        if device:
            device.verified = True
            device.verified_at = datetime.now(timezone.utc)
            db.add(device)
            await db.commit()
            await db.refresh(device)
        return device

    async def update_last_used(self, db: AsyncSession, *, id: UUID) -> None:
        """Update last used timestamp."""
        stmt = (
            update(MFADevice)
            .where(MFADevice.id == id)
            .values(last_used=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()

    async def hard_delete(self, db: AsyncSession, *, id: UUID) -> bool:
        """Remove MFA device."""
        device = await self.get_by_id(db, id=id)
        if device:
            await db.delete(device)
            await db.commit()
            return True
        return False


# ==========================================
# 9. API Key Repository
# ==========================================

class ApiKeyRepository:
    """Data Access Layer for ApiKey model."""

    async def create(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        hashed_key: str,
        expires_at: Optional[datetime] = None
    ) -> ApiKey:
        """Create API Key record."""
        key = ApiKey(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            hashed_key=hashed_key,
            expires_at=expires_at,
        )
        db.add(key)
        await db.commit()
        await db.refresh(key)
        return key

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: Optional[UUID] = None
    ) -> Optional[ApiKey]:
        """Fetch API Key by ID."""
        stmt = select(ApiKey).where(ApiKey.id == id)
        if tenant_id:
            stmt = stmt.where(ApiKey.tenant_id == tenant_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_hashed_key(self, db: AsyncSession, *, hashed_key: str) -> Optional[ApiKey]:
        """Fetch API Key by hashed key string."""
        stmt = select(ApiKey).where(ApiKey.hashed_key == hashed_key, ApiKey.is_active == True)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID
    ) -> List[ApiKey]:
        """Fetch API Keys for user in tenant."""
        stmt = select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.tenant_id == tenant_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_last_used(self, db: AsyncSession, *, id: UUID) -> None:
        """Touch last used timestamp."""
        stmt = (
            update(ApiKey)
            .where(ApiKey.id == id)
            .values(last_used=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()

    async def deactivate(self, db: AsyncSession, *, id: UUID) -> bool:
        """Deactivate API Key."""
        key = await self.get_by_id(db, id=id)
        if key:
            key.is_active = False
            db.add(key)
            await db.commit()
            return True
        return False


# ==========================================
# 10. Trusted Device Repository
# ==========================================

class TrustedDeviceRepository:
    """Data Access Layer for TrustedDevice model."""

    async def create(
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
        """Register trusted device."""
        trusted = TrustedDevice(
            user_id=user_id,
            device_identifier=device_identifier,
            device_name=device_name,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
        )
        db.add(trusted)
        await db.commit()
        await db.refresh(trusted)
        return trusted

    async def get_by_device_identifier(
        self, db: AsyncSession, *, user_id: UUID, device_identifier: str
    ) -> Optional[TrustedDevice]:
        """Fetch device by identifier."""
        stmt = select(TrustedDevice).where(
            TrustedDevice.user_id == user_id,
            TrustedDevice.device_identifier == device_identifier,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, *, user_id: UUID) -> List[TrustedDevice]:
        """Fetch all trusted devices for user."""
        stmt = select(TrustedDevice).where(TrustedDevice.user_id == user_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_last_seen(self, db: AsyncSession, *, id: UUID) -> None:
        """Touch last seen timestamp."""
        stmt = (
            update(TrustedDevice)
            .where(TrustedDevice.id == id)
            .values(last_seen=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()


# ==========================================
# 11. User Preference Repository
# ==========================================

class UserPreferenceRepository:
    """Data Access Layer for UserPreference model."""

    async def create_or_update(
        self, db: AsyncSession, *, user_id: UUID, obj_in: Union[UserPreferenceUpdate, Dict[str, Any]]
    ) -> UserPreference:
        """Upsert user preferences."""
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        res = await db.execute(stmt)
        pref = res.scalar_one_or_none()

        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        if not pref:
            pref = UserPreference(user_id=user_id, **update_data)
        else:
            for field, val in update_data.items():
                if hasattr(pref, field):
                    setattr(pref, field, val)

        db.add(pref)
        await db.commit()
        await db.refresh(pref)
        return pref

    async def get_by_user_id(self, db: AsyncSession, *, user_id: UUID) -> Optional[UserPreference]:
        """Fetch preferences for user."""
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()


# ==========================================
# 12. Electronic Signature Profile Repository
# ==========================================

class ElectronicSignatureProfileRepository:
    """Data Access Layer for ElectronicSignatureProfile model."""

    async def create_or_update(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        obj_in: Union[ElectronicSignatureProfileCreate, ElectronicSignatureProfileUpdate, Dict[str, Any]]
    ) -> ElectronicSignatureProfile:
        """Upsert electronic signature profile."""
        stmt = select(ElectronicSignatureProfile).where(
            ElectronicSignatureProfile.user_id == user_id
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()

        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        if not profile:
            profile = ElectronicSignatureProfile(user_id=user_id, **update_data)
        else:
            for field, val in update_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, val)

        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: UUID
    ) -> Optional[ElectronicSignatureProfile]:
        """Fetch signature profile for user."""
        stmt = select(ElectronicSignatureProfile).where(
            ElectronicSignatureProfile.user_id == user_id
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()


# ==========================================
# Export Repository Singletons
# ==========================================

user_repo = UserRepository()
user_profile_repo = UserProfileRepository()
user_role_repo = UserRoleRepository()
user_session_repo = UserSessionRepository()
refresh_token_repo = RefreshTokenRepository()
password_history_repo = PasswordHistoryRepository()
login_history_repo = LoginHistoryRepository()
mfa_device_repo = MFADeviceRepository()
api_key_repo = ApiKeyRepository()
trusted_device_repo = TrustedDeviceRepository()
user_preference_repo = UserPreferenceRepository()
electronic_signature_profile_repo = ElectronicSignatureProfileRepository()
