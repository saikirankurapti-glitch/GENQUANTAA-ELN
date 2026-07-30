import logging
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
    require_admin,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.identity import UserRoleCreate, UserRoleRead
from app.services.identity.exceptions import UserNotFound
from app.services.identity.user_role_service import user_role_service
from app.services.rbac.exceptions import RoleNotFound

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users/{user_id}/roles/{role_id}", response_model=UserRoleRead, summary="Assign Role to User")
async def assign_role(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    role_id: UUID,
    role_assignment_in: UserRoleCreate,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Assign a role to a user within tenant scope."""
    try:
        return await user_role_service.assign_role_to_user(
            db,
            user_id=user_id,
            role_id=role_id,
            tenant_id=current_tenant.id,
            assigned_by=current_user.id,
            is_primary=role_assignment_in.is_primary,
            expires_at=role_assignment_in.expires_at,
        )
    except (UserNotFound, RoleNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/users/{user_id}/roles/{role_id}", summary="Revoke Role from User")
async def revoke_role(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    role_id: UUID,
    current_user: User = Depends(require_admin),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Revoke a role assignment from a user."""
    try:
        await user_role_service.revoke_role_from_user(
            db, user_id=user_id, role_id=role_id, tenant_id=current_tenant.id
        )
        return {"message": "Role assignment revoked successfully."}
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/users/{user_id}/roles", response_model=List[UserRoleRead], summary="List Roles Assigned to User")
async def list_user_roles(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(require_permission("identity.user.read")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """List all role assignments for a user."""
    try:
        return await user_role_service.list_user_roles(
            db, user_id=user_id, tenant_id=current_tenant.id
        )
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
