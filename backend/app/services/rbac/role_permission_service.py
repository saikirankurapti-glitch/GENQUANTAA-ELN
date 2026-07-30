import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_role import role as role_repo
from app.crud.crud_permission import permission as permission_repo
from app.crud.crud_role_permission import role_permission as role_permission_repo
from app.models.rbac import Role, Permission, RolePermission
from app.services.rbac.exceptions import (
    RoleNotFound,
    PermissionNotFound,
    DuplicatePermissionAssignment,
    TenantIsolationError,
    ValidationError
)

logger = logging.getLogger(__name__)

class RolePermissionService:
    """
    Business Logic Layer governing the assignment and removal of permissions to roles.
    Coordinates multiple repositories to enforce tenant boundaries and existence checks.
    """

    async def validate_role_exists(self, db: AsyncSession, *, role_id: UUID, tenant_id: UUID) -> Role:
        """
        Verify the Role exists and strictly belongs to the requested tenant.
        Prevents assignment to soft-deleted roles.
        """
        # Note: role_repo.get_by_id automatically filters out soft-deleted records.
        role_obj = await role_repo.get_by_id(db, id=role_id)
        if not role_obj:
            raise RoleNotFound(f"Role with ID {role_id} not found or has been deleted.")
            
        if role_obj.tenant_id != tenant_id:
            logger.warning(f"Tenant isolation violation attempt: Role {role_id} (Tenant: {role_obj.tenant_id}) accessed by Tenant {tenant_id}")
            raise TenantIsolationError(f"Role {role_id} does not belong to the current tenant scope.")
            
        return role_obj

    async def validate_permission_exists(self, db: AsyncSession, *, permission_id: UUID) -> Permission:
        """Verify a single Permission exists in the global registry."""
        perm_obj = await permission_repo.get_by_id(db, id=permission_id)
        if not perm_obj:
            raise PermissionNotFound(f"Permission with ID {permission_id} not found.")
        return perm_obj

    async def validate_role_permission(self, db: AsyncSession, *, role_id: UUID, permission_id: UUID) -> None:
        """
        Check if the specific role currently holds the specific permission.
        Throws a ValidationError if they are not linked.
        """
        exists = await role_permission_repo.permission_exists(db, role_id=role_id, permission_id=permission_id)
        if not exists:
            raise ValidationError(f"Role {role_id} does not have Permission {permission_id} assigned.")

    async def get_permissions_for_role(self, db: AsyncSession, *, role_id: UUID, tenant_id: UUID) -> List[Permission]:
        """Fetch all permissions assigned to a role, validating tenant ownership first."""
        await self.validate_role_exists(db, role_id=role_id, tenant_id=tenant_id)
        return await role_permission_repo.get_permissions_for_role(db, role_id=role_id)

    async def get_roles_for_permission(self, db: AsyncSession, *, permission_id: UUID) -> List[Role]:
        """Fetch all roles globally that possess a specific permission."""
        await self.validate_permission_exists(db, permission_id=permission_id)
        return await role_permission_repo.get_roles_for_permission(db, permission_id=permission_id)

    async def assign_permission(
        self, 
        db: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_id: UUID, 
        tenant_id: UUID,
        granted_by: Optional[UUID] = None
    ) -> RolePermission:
        """
        Assign a single permission to a role.
        """
        await self.validate_role_exists(db, role_id=role_id, tenant_id=tenant_id)
        await self.validate_permission_exists(db, permission_id=permission_id)
        
        exists = await role_permission_repo.permission_exists(db, role_id=role_id, permission_id=permission_id)
        if exists:
            logger.warning(f"Duplicate assignment attempt: Permission {permission_id} to Role {role_id}")
            raise DuplicatePermissionAssignment("This permission is already assigned to the role.")
            
        rp = await role_permission_repo.assign_permission(
            db, 
            role_id=role_id, 
            permission_id=permission_id, 
            granted_by=granted_by
        )
        logger.info(f"RolePermissionService: Assigned permission {permission_id} to role {role_id}.")
        return rp

    async def assign_permissions_bulk(
        self, 
        db: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_ids: List[UUID], 
        tenant_id: UUID,
        granted_by: Optional[UUID] = None
    ) -> int:
        """
        Bulk assign multiple permissions to a role.
        """
        if not permission_ids:
            raise ValidationError("Bulk assignment request must contain at least one permission ID.")
            
        await self.validate_role_exists(db, role_id=role_id, tenant_id=tenant_id)
        
        unique_permission_ids = list(set(permission_ids))
        
        # Validate that EVERY requested permission exists globally
        for pid in unique_permission_ids:
            await self.validate_permission_exists(db, permission_id=pid)
            
        count = await role_permission_repo.assign_permissions_bulk(
            db, 
            role_id=role_id, 
            permission_ids=unique_permission_ids, 
            granted_by=granted_by
        )
        logger.info(f"RolePermissionService: Bulk assigned {count} new permissions to role {role_id}.")
        return count

    async def remove_permission(self, db: AsyncSession, *, role_id: UUID, permission_id: UUID, tenant_id: UUID) -> bool:
        """
        Remove a single permission from a role.
        """
        await self.validate_role_exists(db, role_id=role_id, tenant_id=tenant_id)
        await self.validate_permission_exists(db, permission_id=permission_id)
        await self.validate_role_permission(db, role_id=role_id, permission_id=permission_id)
        
        success = await role_permission_repo.remove_permission(db, role_id=role_id, permission_id=permission_id)
        logger.info(f"RolePermissionService: Removed permission {permission_id} from role {role_id}.")
        return success

    async def remove_permissions_bulk(
        self, 
        db: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_ids: List[UUID], 
        tenant_id: UUID
    ) -> int:
        """
        Bulk remove multiple permissions from a role.
        """
        if not permission_ids:
            raise ValidationError("Bulk removal request must contain at least one permission ID.")
            
        await self.validate_role_exists(db, role_id=role_id, tenant_id=tenant_id)
        
        unique_permission_ids = list(set(permission_ids))
        
        count = await role_permission_repo.remove_permissions_bulk(
            db, 
            role_id=role_id, 
            permission_ids=unique_permission_ids
        )
        logger.info(f"RolePermissionService: Bulk removed {count} permissions from role {role_id}.")
        return count

    async def replace_permissions(
        self, 
        db: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_ids: List[UUID], 
        tenant_id: UUID,
        granted_by: Optional[UUID] = None
    ) -> None:
        """
        Completely replace the permission set of a role.
        """
        if not permission_ids:
            raise ValidationError("Permission replacement request must contain at least one permission ID. Use removal endpoints to clear all.")
            
        await self.validate_role_exists(db, role_id=role_id, tenant_id=tenant_id)
        
        unique_permission_ids = list(set(permission_ids))
        
        for pid in unique_permission_ids:
            await self.validate_permission_exists(db, permission_id=pid)
            
        await role_permission_repo.replace_permissions(
            db, 
            role_id=role_id, 
            permission_ids=unique_permission_ids, 
            granted_by=granted_by
        )
        logger.info(f"RolePermissionService: Replaced all permissions for role {role_id} with {len(unique_permission_ids)} new permissions.")

role_permission_service = RolePermissionService()
