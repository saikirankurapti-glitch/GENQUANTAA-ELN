import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac import Permission
from app.schemas.rbac import PermissionCreate, PermissionUpdate

logger = logging.getLogger(__name__)

class CRUDPermission:
    """
    Repository Layer for the Permission Entity.
    Permissions are GLOBAL and do not utilize tenant isolation.
    """

    async def create(self, db: AsyncSession, *, obj_in: PermissionCreate) -> Permission:
        """
        Create a new Permission in the database.
        
        Args:
            db (AsyncSession): SQLAlchemy async session.
            obj_in (PermissionCreate): Schema containing permission data.
            
        Returns:
            Permission: The created permission database object.
        """
        db_obj = Permission(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created Permission: {db_obj.code}")
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Permission, obj_in: Union[PermissionUpdate, Dict[str, Any]]) -> Permission:
        """
        Update an existing Permission.
        
        Args:
            db (AsyncSession): SQLAlchemy async session.
            db_obj (Permission): The database object to update.
            obj_in (Union[PermissionUpdate, Dict[str, Any]]): Data to apply to the object.
            
        Returns:
            Permission: The updated permission database object.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Updated Permission: {db_obj.id}")
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[Permission]:
        """
        Hard delete a Permission (Permissions do not use soft delete).
        
        Args:
            db (AsyncSession): SQLAlchemy async session.
            id (UUID): The ID of the permission.
            
        Returns:
            Optional[Permission]: The deleted permission object, or None if not found.
        """
        obj = await self.get_by_id(db=db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
            logger.info(f"Hard deleted Permission: {id}")
        return obj

    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[Permission]:
        """Get a Permission by its UUID."""
        stmt = select(Permission).where(Permission.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, *, code: str) -> Optional[Permission]:
        """Get a Permission by its unique code."""
        stmt = select(Permission).where(Permission.code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, db: AsyncSession, *, code: str) -> bool:
        """Check if a Permission with the given code exists."""
        stmt = select(select(Permission).where(Permission.code == code).exists())
        result = await db.execute(stmt)
        return result.scalar()

    async def count(self, db: AsyncSession) -> int:
        """Count total Permissions in the system."""
        stmt = select(func.count(Permission.id))
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_all(self, db: AsyncSession) -> List[Permission]:
        """Get all Permissions (unpaginated)."""
        stmt = select(Permission)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self, 
        db: AsyncSession, 
        *, 
        query: str,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "code",
        sort_order: str = "asc"
    ) -> Tuple[List[Permission], int]:
        """
        Search Permissions using ILIKE across module, resource, action, code, or description.
        Returns paginated results and total count.
        """
        stmt = select(Permission)
        
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Permission.module.ilike(search_term),
                    Permission.resource.ilike(search_term),
                    Permission.action.ilike(search_term),
                    Permission.code.ilike(search_term),
                    Permission.description.ilike(search_term)
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply Sorting
        if hasattr(Permission, sort_by):
            sort_attr = getattr(Permission, sort_by)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())

        # Apply Pagination
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())
        
        return items, total

    async def filter(
        self,
        db: AsyncSession,
        *,
        module: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "code",
        sort_order: str = "asc"
    ) -> Tuple[List[Permission], int]:
        """
        Filter Permissions using exact matching on specific fields.
        Returns paginated results and total count.
        """
        stmt = select(Permission)
        
        if module:
            stmt = stmt.where(Permission.module == module)
        if resource:
            stmt = stmt.where(Permission.resource == resource)
        if action:
            stmt = stmt.where(Permission.action == action)
            
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Apply Sorting
        if hasattr(Permission, sort_by):
            sort_attr = getattr(Permission, sort_by)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())
        
        # Apply Pagination
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size)
        
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        
        return items, total

permission = CRUDPermission()
