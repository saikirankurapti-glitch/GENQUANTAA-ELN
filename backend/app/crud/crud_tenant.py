from typing import Any, Dict, Optional, Union, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate

class CRUDTenant:
    async def get(self, db: AsyncSession, id: Any) -> Optional[Tenant]:
        result = await db.execute(select(Tenant).filter(Tenant.id == id, Tenant.is_deleted == False))
        return result.scalars().first()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Tenant]:
        result = await db.execute(select(Tenant).filter(Tenant.code == code, Tenant.is_deleted == False))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Tenant]:
        result = await db.execute(select(Tenant).filter(Tenant.is_deleted == False).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: TenantCreate) -> Tenant:
        db_obj = Tenant(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Tenant, obj_in: Union[TenantUpdate, Dict[str, Any]]) -> Tenant:
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
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Tenant:
        # Soft delete mechanism
        obj = await self.get(db=db, id=id)
        if obj:
            obj.is_deleted = True
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj

tenant = CRUDTenant()
