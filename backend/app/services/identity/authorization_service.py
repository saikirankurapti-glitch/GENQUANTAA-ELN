import logging
from datetime import datetime, timezone
from typing import List, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import user_repo, user_role_repo
from app.services.identity.exceptions import UnauthorizedAction, UserNotFound
from app.services.rbac.role_permission_service import role_permission_service

logger = logging.getLogger(__name__)


class AuthorizationService:
    """Service bridge integrating Identity User context with RBAC permission evaluations."""

    async def get_user_permission_codes(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID
    ) -> Set[str]:
        """Fetch all granted permission codes for a user based on their assigned active roles."""
        user = await user_repo.get_by_id(db, id=user_id, tenant_id=tenant_id)
        if not user or not user.is_active or user.is_deleted:
            raise UserNotFound(f"User {user_id} not active or not found in tenant.")

        user_roles = await user_role_repo.get_by_user_id(db, user_id=user_id)
        permission_codes: Set[str] = set()

        for user_role in user_roles:
            if user_role.is_active and (user_role.expires_at is None or user_role.expires_at > datetime.now(timezone.utc)):
                perms = await role_permission_service.get_role_permissions(
                    db, role_id=user_role.role_id, tenant_id=tenant_id
                )
                for perm in perms:
                    permission_codes.add(perm.code)

        return permission_codes

    async def has_permission(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID, required_permission: str
    ) -> bool:
        """Check if user is explicitly granted a specific permission code."""
        permissions = await self.get_user_permission_codes(db, user_id=user_id, tenant_id=tenant_id)
        return required_permission in permissions

    async def require_permission(
        self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID, required_permission: str
    ) -> None:
        """Enforce permission requirement or raise UnauthorizedAction exception."""
        if not await self.has_permission(db, user_id=user_id, tenant_id=tenant_id, required_permission=required_permission):
            raise UnauthorizedAction(f"User does not possess required permission '{required_permission}'.")


authorization_service = AuthorizationService()
