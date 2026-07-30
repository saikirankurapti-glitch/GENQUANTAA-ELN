import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, insert, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac import RolePermission, Permission, Role

logger = logging.getLogger(__name__)

class CRUDRolePermission:
    """
    Repository Layer for Many-to-Many Role to Permission assignments.
    Manages persistence logic strictly; no business validation occurs here.
    """

    async def permission_exists(self, db: AsyncSession, *, role_id: UUID, permission_id: UUID) -> bool:
        """Check if a specific permission is already assigned to a role."""
        stmt = select(select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).exists())
        result = await db.execute(stmt)
        return result.scalar()

    async def role_has_permission(self, db: AsyncSession, *, role_id: UUID, permission_code: str) -> bool:
        """Check if a role has a permission by its string code via JOIN."""
        stmt = select(select(RolePermission).join(Permission).where(
            RolePermission.role_id == role_id,
            Permission.code == permission_code
        ).exists())
        result = await db.execute(stmt)
        return result.scalar()

    async def get_permissions_for_role(self, db: AsyncSession, *, role_id: UUID) -> List[Permission]:
        """Fetch all Permission models associated with a Role."""
        stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == role_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_roles_for_permission(self, db: AsyncSession, *, permission_id: UUID) -> List[Role]:
        """Fetch all active Role models associated with a Permission."""
        stmt = select(Role).join(RolePermission).where(
            RolePermission.permission_id == permission_id, 
            Role.is_deleted == False
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_permissions(self, db: AsyncSession, *, role_id: UUID) -> int:
        """Count how many permissions a role has."""
        stmt = select(func.count(RolePermission.permission_id)).where(RolePermission.role_id == role_id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def assign_permission(
        self, 
        db: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_id: UUID,
        granted_by: Optional[UUID] = None
    ) -> Optional[RolePermission]:
        """Assign a single permission to a role."""
        exists = await self.permission_exists(db, role_id=role_id, permission_id=permission_id)
        if exists:
            return None
            
        rp = RolePermission(
            role_id=role_id, 
            permission_id=permission_id, 
            granted_by=granted_by,
            granted_at=datetime.now(timezone.utc)
        )
        db.add(rp)
        await db.commit()
        await db.refresh(rp)
        logger.info(f"Assigned permission {permission_id} to role {role_id}")
        return rp

    async def assign_permissions_bulk(
        self, 
        session: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_ids: List[UUID],
        granted_by: Optional[UUID] = None
    ) -> int:
        """Assign multiple permissions to a role atomically."""
        if not permission_ids:
            return 0
            
        # Deduplicate incoming request
        unique_permission_ids = list(set(permission_ids))
            
        # Get existing to prevent duplicates
        stmt = select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        result = await session.execute(stmt)
        existing_ids = set(result.scalars().all())
        
        to_insert = [pid for pid in unique_permission_ids if pid not in existing_ids]
        
        if not to_insert:
            return 0

        # Create bulk insert records
        records = [
            {
                "role_id": role_id,
                "permission_id": pid,
                "granted_by": granted_by,
                "granted_at": datetime.now(timezone.utc)
            }
            for pid in to_insert
        ]
        
        try:
            # Enforce strict atomicity
            async with session.begin():
                await session.execute(insert(RolePermission), records)
            logger.info(f"Bulk assigned {len(to_insert)} permissions to role {role_id}")
            return len(to_insert)
        except Exception as e:
            logger.error(f"Failed to bulk assign permissions: {e}")
            raise

    async def remove_permission(self, db: AsyncSession, *, role_id: UUID, permission_id: UUID) -> bool:
        """Remove a single permission from a role."""
        stmt = delete(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
        result = await db.execute(stmt)
        await db.commit()
        
        success = result.rowcount > 0
        if success:
            logger.info(f"Removed permission {permission_id} from role {role_id}")
        return success

    async def remove_permissions_bulk(
        self, 
        session: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_ids: List[UUID]
    ) -> int:
        """Remove multiple permissions from a role atomically."""
        if not permission_ids:
            return 0
            
        stmt = delete(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id.in_(permission_ids)
        )
        
        try:
            async with session.begin():
                result = await session.execute(stmt)
            deleted_count = result.rowcount
            logger.info(f"Bulk removed {deleted_count} permissions from role {role_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to bulk remove permissions: {e}")
            raise

    async def replace_permissions(
        self, 
        session: AsyncSession, 
        *, 
        role_id: UUID, 
        permission_ids: List[UUID],
        granted_by: Optional[UUID] = None
    ) -> None:
        """
        Replace all existing permissions for a role with a new set atomically.
        """
        unique_permission_ids = list(set(permission_ids))
        
        try:
            async with session.begin():
                # 1. Delete all existing
                del_stmt = delete(RolePermission).where(RolePermission.role_id == role_id)
                await session.execute(del_stmt)
                
                # 2. Insert new ones
                if unique_permission_ids:
                    records = [
                        {
                            "role_id": role_id,
                            "permission_id": pid,
                            "granted_by": granted_by,
                            "granted_at": datetime.now(timezone.utc)
                        }
                        for pid in unique_permission_ids
                    ]
                    await session.execute(insert(RolePermission), records)
                    
            logger.info(f"Replaced permissions for role {role_id} with {len(unique_permission_ids)} new permissions")
        except Exception as e:
            logger.error(f"Failed to replace permissions for role {role_id}: {e}")
            raise

role_permission = CRUDRolePermission()
