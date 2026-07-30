import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import user_repo, user_role_repo
from app.crud.crud_role import role as role_repo
from app.models.identity import UserRole
from app.services.identity.exceptions import UserNotFound
from app.services.rbac.exceptions import RoleNotFound

logger = logging.getLogger(__name__)


class UserRoleService:
    """Service governing role assignments and revocations to Users."""

    async def assign_role_to_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
        assigned_by: Optional[UUID] = None,
        is_primary: bool = False,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """Assign a role to a user within tenant scope."""
        # Ensure user exists within tenant
        user = await user_repo.get_by_id(db, id=user_id, tenant_id=tenant_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found in tenant.")

        # Ensure role exists within tenant
        role_obj = await role_repo.get_by_id(db, id=role_id, tenant_id=tenant_id)
        if not role_obj:
            raise RoleNotFound(f"Role {role_id} not found in tenant.")

        # Check existing mapping
        existing = await user_role_repo.get_by_user_and_role(db, user_id=user_id, role_id=role_id)
        if existing:
            return existing

        user_role = await user_role_repo.create(
            db,
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            is_primary=is_primary,
            expires_at=expires_at,
        )
        logger.info(f"UserRoleService: Assigned role {role_id} to user {user_id}")
        return user_role

    async def revoke_role_from_user(
        self, db: AsyncSession, *, user_id: UUID, role_id: UUID, tenant_id: UUID
    ) -> bool:
        """Revoke a role from a user."""
        user = await user_repo.get_by_id(db, id=user_id, tenant_id=tenant_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found in tenant.")

        revoked = await user_role_repo.hard_delete(db, user_id=user_id, role_id=role_id)
        if revoked:
            logger.info(f"UserRoleService: Revoked role {role_id} from user {user_id}")
        return revoked

    async def list_user_roles(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID
    ) -> List[UserRole]:
        """Fetch active role assignments for user."""
        user = await user_repo.get_by_id(db, id=user_id, tenant_id=tenant_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found in tenant.")

        return await user_role_repo.get_by_user_id(db, user_id=user_id)


user_role_service = UserRoleService()
