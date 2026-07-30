import logging
from uuid import UUID
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    require_permission,
    get_current_active_user,
    get_current_tenant
)
from app.schemas.rbac import (
    RolePermissionAssign,
    RolePermissionResponse,
    PermissionRead,
    RoleRead
)
from app.services.rbac.role_permission_service import role_permission_service
from app.services.rbac.exceptions import (
    RoleNotFound,
    PermissionNotFound,
    DuplicatePermissionAssignment,
    TenantIsolationError,
    ValidationError
)
from app.models.identity import User
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_201_CREATED,
    summary="Assign permissions to a role",
    description="Assign one or multiple global permissions to a specific role within the tenant."
)
async def assign_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    assignment_in: RolePermissionAssign,
    current_user: User = Depends(require_permission("rbac.role_permission.assign")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Assign permissions to a role."""
    try:
        if len(assignment_in.permission_ids) == 1:
            await role_permission_service.assign_permission(
                db, 
                role_id=role_id, 
                permission_id=assignment_in.permission_ids[0],
                tenant_id=current_tenant.id,
                granted_by=current_user.id
            )
            return {"detail": "Permission assigned successfully."}
        else:
            count = await role_permission_service.assign_permissions_bulk(
                db,
                role_id=role_id,
                permission_ids=assignment_in.permission_ids,
                tenant_id=current_tenant.id,
                granted_by=current_user.id
            )
            return {"detail": f"Successfully assigned {count} permissions."}
    except (RoleNotFound, PermissionNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicatePermissionAssignment as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except TenantIsolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_200_OK,
    summary="Replace all permissions for a role",
    description="Completely replace the existing permission set of a role with a new one."
)
async def replace_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    assignment_in: RolePermissionAssign,
    current_user: User = Depends(require_permission("rbac.role_permission.replace")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Replace all permissions for a role."""
    try:
        await role_permission_service.replace_permissions(
            db,
            role_id=role_id,
            permission_ids=assignment_in.permission_ids,
            tenant_id=current_tenant.id,
            granted_by=current_user.id
        )
        return {"detail": "Permissions replaced successfully."}
    except (RoleNotFound, PermissionNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantIsolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a single permission from a role"
)
async def remove_permission(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    permission_id: UUID,
    current_user: User = Depends(require_permission("rbac.role_permission.remove")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Remove a single permission from a role."""
    try:
        await role_permission_service.remove_permission(
            db,
            role_id=role_id,
            permission_id=permission_id,
            tenant_id=current_tenant.id
        )
        return {"detail": "Permission removed successfully."}
    except (RoleNotFound, PermissionNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantIsolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_200_OK,
    summary="Bulk remove permissions from a role",
    description="Provide a payload containing a list of permission_ids to remove from the role."
)
async def bulk_remove_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    assignment_in: RolePermissionAssign,
    current_user: User = Depends(require_permission("rbac.role_permission.remove")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Bulk remove permissions from a role."""
    try:
        count = await role_permission_service.remove_permissions_bulk(
            db,
            role_id=role_id,
            permission_ids=assignment_in.permission_ids,
            tenant_id=current_tenant.id
        )
        return {"detail": f"Successfully removed {count} permissions."}
    except (RoleNotFound, PermissionNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantIsolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/roles/{role_id}/permissions",
    response_model=List[PermissionRead],
    summary="Get all permissions assigned to a role"
)
async def get_permissions_for_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: UUID,
    current_user: User = Depends(require_permission("rbac.role_permission.read")),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Return all permissions assigned to a role."""
    try:
        return await role_permission_service.get_permissions_for_role(
            db, 
            role_id=role_id, 
            tenant_id=current_tenant.id
        )
    except RoleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantIsolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/permissions/{permission_id}/roles",
    response_model=List[RoleRead],
    summary="Get all roles containing a permission"
)
async def get_roles_for_permission(
    *,
    db: AsyncSession = Depends(get_db),
    permission_id: UUID,
    current_user: User = Depends(require_permission("rbac.role_permission.read"))
    # Note: Tenant context is intentionally omitted here as we are querying from a global permission 
    # standpoint. However, the repository filters return roles across all tenants. 
    # Further filtering could be applied if necessary.
) -> Any:
    """Return all roles containing the permission globally."""
    try:
        return await role_permission_service.get_roles_for_permission(
            db, 
            permission_id=permission_id
        )
    except PermissionNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
