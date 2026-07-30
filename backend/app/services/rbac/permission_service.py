import logging
import re
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_permission import permission as permission_repo
from app.models.rbac import Permission
from app.schemas.rbac import PermissionCreate, PermissionUpdate
from app.services.rbac.exceptions import (
    PermissionNotFound,
    PermissionAlreadyExists,
    InvalidPermissionCode,
    ValidationError
)

logger = logging.getLogger(__name__)

class PermissionService:
    """
    Business Logic Layer for the Permission domain.
    Enforces format rules, normalization, and global uniqueness.
    """

    def _normalize_and_validate_format(self, module: str, resource: str, action: str, code: str) -> str:
        """
        Normalizes inputs to lowercase and stripped, then validates the pattern.
        Code must strictly match 'module.resource.action'.
        """
        if not module or not str(module).strip():
            raise ValidationError("Module cannot be empty.")
        if not resource or not str(resource).strip():
            raise ValidationError("Resource cannot be empty.")
        if not action or not str(action).strip():
            raise ValidationError("Action cannot be empty.")

        mod = module.strip().lower()
        res = resource.strip().lower()
        act = action.strip().lower()
        
        expected_code = f"{mod}.{res}.{act}"
        provided_code = (code or "").strip().lower()

        if expected_code != provided_code:
            logger.warning(f"Invalid permission code format: expected '{expected_code}', got '{provided_code}'")
            raise InvalidPermissionCode(f"Permission code must match the pattern '{mod}.{res}.{act}'. Got '{provided_code}'.")
            
        return expected_code

    async def validate_unique_permission_code(self, db: AsyncSession, *, code: str) -> None:
        """Ensure a permission code is completely unique globally."""
        if await permission_repo.exists(db, code=code):
            logger.warning(f"Permission uniqueness validation failed for code: {code}")
            raise PermissionAlreadyExists(f"Permission with code '{code}' already exists.")

    async def validate_permission_exists(self, db: AsyncSession, *, id: UUID) -> Permission:
        """Fetch and validate a permission exists by ID."""
        perm_obj = await permission_repo.get_by_id(db, id=id)
        if not perm_obj:
            logger.warning(f"Permission existence validation failed for id: {id}")
            raise PermissionNotFound(f"Permission with ID {id} not found.")
        return perm_obj

    async def create_permission(self, db: AsyncSession, *, obj_in: PermissionCreate) -> Permission:
        """
        Create a new Permission after enforcing strict business rules and normalization.
        """
        normalized_code = self._normalize_and_validate_format(
            module=obj_in.module,
            resource=obj_in.resource,
            action=obj_in.action,
            code=obj_in.code
        )
        
        await self.validate_unique_permission_code(db, code=normalized_code)
        
        # Override incoming code with safely normalized code
        obj_in.code = normalized_code
        obj_in.module = obj_in.module.strip().lower()
        obj_in.resource = obj_in.resource.strip().lower()
        obj_in.action = obj_in.action.strip().lower()
        
        new_perm = await permission_repo.create(db, obj_in=obj_in)
        logger.info(f"PermissionService: Successfully created permission '{new_perm.code}'.")
        return new_perm

    async def get_permission(self, db: AsyncSession, *, id: UUID) -> Permission:
        """
        Retrieve a permission by ID.
        """
        return await self.validate_permission_exists(db, id=id)

    async def update_permission(self, db: AsyncSession, *, id: UUID, obj_in: PermissionUpdate) -> Permission:
        """
        Update an existing permission, re-validating uniqueness and formatting if changed.
        """
        perm_obj = await self.validate_permission_exists(db, id=id)
        
        # Calculate new theoretical state for validation
        new_module = obj_in.module if obj_in.module is not None else perm_obj.module
        new_resource = obj_in.resource if obj_in.resource is not None else perm_obj.resource
        new_action = obj_in.action if obj_in.action is not None else perm_obj.action
        new_code = obj_in.code if obj_in.code is not None else perm_obj.code
        
        normalized_code = self._normalize_and_validate_format(
            module=new_module,
            resource=new_resource,
            action=new_action,
            code=new_code
        )

        if normalized_code != perm_obj.code:
            await self.validate_unique_permission_code(db, code=normalized_code)
            obj_in.code = normalized_code
            
        if obj_in.module is not None: obj_in.module = obj_in.module.strip().lower()
        if obj_in.resource is not None: obj_in.resource = obj_in.resource.strip().lower()
        if obj_in.action is not None: obj_in.action = obj_in.action.strip().lower()

        updated_perm = await permission_repo.update(db, db_obj=perm_obj, obj_in=obj_in)
        logger.info(f"PermissionService: Successfully updated permission '{updated_perm.code}'.")
        return updated_perm

    async def delete_permission(self, db: AsyncSession, *, id: UUID) -> Permission:
        """
        Hard delete a permission.
        """
        perm_obj = await self.validate_permission_exists(db, id=id)
        
        deleted_perm = await permission_repo.delete(db, id=id)
        logger.info(f"PermissionService: Successfully deleted permission '{perm_obj.code}'.")
        return deleted_perm

    async def list_permissions(self, db: AsyncSession) -> List[Permission]:
        """Fetch all permissions."""
        return await permission_repo.get_all(db)

    async def search_permissions(
        self, 
        db: AsyncSession, 
        *, 
        query: str, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Permission], int]:
        """Search permissions via full-text ILIKE proxy."""
        return await permission_repo.search(
            db, 
            query=query, 
            page=page, 
            page_size=page_size
        )

permission_service = PermissionService()
