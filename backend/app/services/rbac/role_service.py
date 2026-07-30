import logging
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_role import role as role_repo
from app.models.rbac import Role
from app.schemas.rbac import RoleCreate, RoleUpdate
from app.services.rbac.exceptions import (
    RoleNotFound,
    RoleAlreadyExists,
    SystemRoleModificationError,
    SystemRoleDeletionError
)

logger = logging.getLogger(__name__)

class RoleService:
    """
    Business Logic Layer for the Role domain.
    Enforces tenant boundaries, system role protections, and duplicate prevention.
    """

    async def validate_unique_role_code(self, db: AsyncSession, *, code: str, tenant_id: UUID) -> None:
        """Ensure a role code is completely unique within the tenant."""
        if await role_repo.exists_by_code(db, code=code, tenant_id=tenant_id):
            raise RoleAlreadyExists(f"Role with code '{code}' already exists in this tenant.")

    async def validate_unique_role_name(self, db: AsyncSession, *, name: str, tenant_id: UUID) -> None:
        """Ensure a role name is completely unique within the tenant."""
        if await role_repo.exists_by_name(db, name=name, tenant_id=tenant_id):
            raise RoleAlreadyExists(f"Role with name '{name}' already exists in this tenant.")

    def prevent_system_role_modification(self, role_obj: Role) -> None:
        """System roles are protected and cannot be modified by users."""
        if getattr(role_obj, "is_system", False):
            raise SystemRoleModificationError(f"System role '{role_obj.code}' cannot be modified.")

    def prevent_system_role_deletion(self, role_obj: Role) -> None:
        """System roles are critical to the platform and cannot be deleted."""
        if getattr(role_obj, "is_system", False):
            raise SystemRoleDeletionError(f"System role '{role_obj.code}' cannot be deleted.")

    async def create_role(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        """
        Create a new Role after enforcing business rules.
        """
        await self.validate_unique_role_code(db, code=obj_in.code, tenant_id=obj_in.tenant_id)
        await self.validate_unique_role_name(db, name=obj_in.name, tenant_id=obj_in.tenant_id)
        
        new_role = await role_repo.create(db, obj_in=obj_in)
        logger.info(f"RoleService: Successfully created role '{new_role.code}'.")
        return new_role

    async def get_role(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> Role:
        """
        Retrieve a role by ID, strictly enforcing tenant isolation.
        """
        role_obj = await role_repo.get_by_id(db, id=id, tenant_id=tenant_id)
        if not role_obj:
            raise RoleNotFound(f"Role with ID {id} not found in the current tenant scope.")
        return role_obj

    async def update_role(self, db: AsyncSession, *, id: UUID, tenant_id: UUID, obj_in: RoleUpdate) -> Role:
        """
        Update an existing role, validating uniqueness of incoming changes and protecting system roles.
        """
        role_obj = await self.get_role(db, id=id, tenant_id=tenant_id)
        
        self.prevent_system_role_modification(role_obj)

        if obj_in.code and obj_in.code != role_obj.code:
            await self.validate_unique_role_code(db, code=obj_in.code, tenant_id=tenant_id)
            
        if obj_in.name and obj_in.name != role_obj.name:
            await self.validate_unique_role_name(db, name=obj_in.name, tenant_id=tenant_id)

        updated_role = await role_repo.update(db, db_obj=role_obj, obj_in=obj_in)
        logger.info(f"RoleService: Successfully updated role '{updated_role.code}'.")
        return updated_role

    async def delete_role(self, db: AsyncSession, *, id: UUID, tenant_id: UUID) -> Role:
        """
        Soft delete a role, ensuring it is not a system role.
        """
        role_obj = await self.get_role(db, id=id, tenant_id=tenant_id)
        
        self.prevent_system_role_deletion(role_obj)
        
        deleted_role = await role_repo.soft_delete(db, id=id)
        logger.info(f"RoleService: Successfully deleted role '{deleted_role.code}'.")
        return deleted_role

    async def list_roles(self, db: AsyncSession, *, tenant_id: UUID) -> List[Role]:
        """Fetch all roles for a tenant."""
        return await role_repo.get_all(db, tenant_id=tenant_id)

    async def search_roles(
        self, 
        db: AsyncSession, 
        *, 
        tenant_id: UUID, 
        query: str, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Role], int]:
        """Search roles via full-text ILIKE proxy."""
        return await role_repo.search(
            db, 
            tenant_id=tenant_id, 
            query=query, 
            page=page, 
            page_size=page_size
        )

role_service = RoleService()
