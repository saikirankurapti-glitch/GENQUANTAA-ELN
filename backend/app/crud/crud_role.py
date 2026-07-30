import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac import Role
from app.schemas.rbac import RoleCreate, RoleUpdate

logger = logging.getLogger(__name__)

class CRUDRole:
    """Repository Layer for Role Entity"""
    
    async def create(self, db: AsyncSession, *, obj_in: RoleCreate) -> Role:
        """Create a new Role in the database."""
        db_obj = Role(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created Role {db_obj.code} for Tenant {db_obj.tenant_id}")
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Role, obj_in: Union[RoleUpdate, Dict[str, Any]]) -> Role:
        """Update an existing Role."""
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
        logger.info(f"Updated Role {db_obj.id}")
        return db_obj

    async def soft_delete(self, db: AsyncSession, *, id: UUID) -> Optional[Role]:
        """Soft delete a Role by setting is_deleted=True and deleted_at."""
        obj = await self.get_by_id(db=db, id=id)
        if obj:
            obj.is_deleted = True
            obj.deleted_at = datetime.now(timezone.utc)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            logger.info(f"Soft deleted Role {id}")
        return obj

    async def get_by_id(self, db: AsyncSession, *, id: UUID, tenant_id: Optional[UUID] = None) -> Optional[Role]:
        """Get a Role by ID, ignoring soft deleted records. Optionally scoped by tenant."""
        stmt = select(Role).where(Role.id == id, Role.is_deleted == False)
        if tenant_id:
            stmt = stmt.where(Role.tenant_id == tenant_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, *, code: str, tenant_id: UUID) -> Optional[Role]:
        """Get a Role by unique code within a tenant."""
        stmt = select(Role).where(Role.code == code, Role.tenant_id == tenant_id, Role.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, *, name: str, tenant_id: UUID) -> Optional[Role]:
        """Get a Role by name within a tenant."""
        stmt = select(Role).where(Role.name == name, Role.tenant_id == tenant_id, Role.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_code(self, db: AsyncSession, *, code: str, tenant_id: UUID) -> bool:
        """Check if a Role with the given code exists within the tenant."""
        stmt = select(select(Role).where(Role.code == code, Role.tenant_id == tenant_id, Role.is_deleted == False).exists())
        result = await db.execute(stmt)
        return result.scalar()

    async def exists_by_name(self, db: AsyncSession, *, name: str, tenant_id: UUID) -> bool:
        """Check if a Role with the given name exists within the tenant."""
        stmt = select(select(Role).where(Role.name == name, Role.tenant_id == tenant_id, Role.is_deleted == False).exists())
        result = await db.execute(stmt)
        return result.scalar()

    async def get_all(self, db: AsyncSession, *, tenant_id: UUID) -> List[Role]:
        """Get all active Roles for a tenant."""
        stmt = select(Role).where(Role.tenant_id == tenant_id, Role.is_deleted == False)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self, 
        db: AsyncSession, 
        *, 
        tenant_id: UUID,
        query: str,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Role], int]:
        """Search Roles by name, code, or description with pagination and sorting."""
        stmt = select(Role).where(Role.tenant_id == tenant_id, Role.is_deleted == False)
        
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Role.name.ilike(search_term),
                    Role.code.ilike(search_term),
                    Role.description.ilike(search_term)
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Sorting
        if hasattr(Role, sort_by):
            sort_attr = getattr(Role, sort_by)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())

        # Pagination
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())
        
        return items, total

    async def filter(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        status: Optional[str] = None,
        is_system: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Role], int]:
        """Filter Roles with precise criteria with pagination."""
        stmt = select(Role).where(Role.tenant_id == tenant_id, Role.is_deleted == False)
        
        if status:
            stmt = stmt.where(Role.status == status)
        if is_system is not None:
            stmt = stmt.where(Role.is_system == is_system)
            
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()
        
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size)
        
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        return items, total

role = CRUDRole()
