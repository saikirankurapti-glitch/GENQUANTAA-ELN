import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import user_profile_repo, user_repo
from app.db.enums import UserStatus
from app.models.identity import User
from app.schemas.identity import UserCreate, UserProfileUpdate, UserUpdate
from app.services.identity.exceptions import (
    UserAlreadyExists,
    UserNotFound,
)
from app.services.identity.password_service import password_service

logger = logging.getLogger(__name__)


class UserService:
    """Business Logic Layer for User lifecycle management, activation, and lockout control."""

    async def validate_uniqueness(self, db: AsyncSession, *, username: str, email: str, tenant_id: UUID) -> None:
        """Ensure username and email are unique within the target tenant."""
        if await user_repo.exists_by_username(db, username=username, tenant_id=tenant_id):
            raise UserAlreadyExists(f"Username '{username}' is already taken in this tenant.")
        if await user_repo.exists_by_email(db, email=email, tenant_id=tenant_id):
            raise UserAlreadyExists(f"Email '{email}' is already registered in this tenant.")

    async def register_user(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Register a new user after enforcing business rules and password policy."""
        await self.validate_uniqueness(
            db, username=obj_in.username, email=obj_in.email, tenant_id=obj_in.tenant_id
        )
        password_service.validate_complexity(obj_in.password)

        pwd_hash = password_service.hash_password(obj_in.password)
        new_user = await user_repo.create(db, obj_in=obj_in, password_hash=pwd_hash)
        
        logger.info(f"UserService: Registered new user '{new_user.username}' for tenant '{new_user.tenant_id}'")
        return new_user

    async def get_user_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_relations: bool = True
    ) -> User:
        """Retrieve user by ID with tenant scoping."""
        user = await user_repo.get_by_id(
            db, id=id, tenant_id=tenant_id, include_relations=include_relations
        )
        if not user:
            raise UserNotFound(f"User with ID {id} not found in the specified tenant.")
        return user

    async def get_user_by_username(
        self, db: AsyncSession, *, username: str, tenant_id: UUID
    ) -> User:
        """Retrieve user by username."""
        user = await user_repo.get_by_username(db, username=username, tenant_id=tenant_id)
        if not user:
            raise UserNotFound(f"User '{username}' not found.")
        return user

    async def update_user(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, obj_in: UserUpdate
    ) -> User:
        """Update user fields, ensuring tenant boundaries."""
        user = await self.get_user_by_id(db, id=id, tenant_id=tenant_id)
        updated_user = await user_repo.update(db, db_obj=user, obj_in=obj_in)
        logger.info(f"UserService: Updated user {id}")
        return updated_user

    async def update_profile(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID, obj_in: UserProfileUpdate
    ) -> User:
        """Update or create user profile."""
        user = await self.get_user_by_id(db, id=user_id, tenant_id=tenant_id, include_relations=True)
        profile = user.profile
        if not profile:
            profile = await user_profile_repo.create(db, obj_in=obj_in, user_id=user_id)
        else:
            profile = await user_profile_repo.update(db, db_obj=profile, obj_in=obj_in)

        # Refresh user object to include updated profile
        return await self.get_user_by_id(db, id=user_id, tenant_id=tenant_id, include_relations=True)

    async def activate_user(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> User:
        """Activate user account."""
        user = await self.get_user_by_id(db, id=id, tenant_id=tenant_id)
        return await user_repo.update(
            db, db_obj=user, obj_in={"is_active": True, "status": UserStatus.ACTIVE}
        )

    async def deactivate_user(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> User:
        """Deactivate user account."""
        user = await self.get_user_by_id(db, id=id, tenant_id=tenant_id)
        return await user_repo.update(
            db, db_obj=user, obj_in={"is_active": False, "status": UserStatus.INACTIVE}
        )

    async def lock_user(self, db: AsyncSession, *, id: UUID, tenant_id: UUID, lock_until: Optional[datetime] = None) -> User:
        """Manually or automatically lock user account."""
        user = await self.get_user_by_id(db, id=id, tenant_id=tenant_id)
        return await user_repo.update(
            db, db_obj=user, obj_in={"is_locked": True, "locked_until": lock_until}
        )

    async def unlock_user(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> User:
        """Unlock user account and reset failed attempts counter."""
        user = await self.get_user_by_id(db, id=id, tenant_id=tenant_id)
        return await user_repo.update(
            db,
            db_obj=user,
            obj_in={"is_locked": False, "failed_login_attempts": 0, "locked_until": None},
        )

    async def delete_user(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, deleted_by: Optional[UUID] = None
    ) -> User:
        """Soft delete user account for GxP/Part 11 compliance."""
        user = await self.get_user_by_id(db, id=id, tenant_id=tenant_id)
        deleted_user = await user_repo.soft_delete(
            db, id=id, tenant_id=tenant_id, deleted_by=deleted_by
        )
        logger.info(f"UserService: Soft deleted user {id}")
        return deleted_user

    async def search_users(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        query: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[User], int]:
        """Search and paginate user records."""
        return await user_repo.search(
            db,
            tenant_id=tenant_id,
            query=query,
            organization_id=organization_id,
            status=status,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )


user_service = UserService()
