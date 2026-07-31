from typing import Any, Dict, Optional, Union, List
from uuid import UUID
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate

class CRUDTenant:
    async def get(self, id: UUID) -> Optional[Tenant]:
        return await Tenant.find_one({"_id": id, "is_deleted": False})

    async def get_by_code(self, code: str) -> Optional[Tenant]:
        return await Tenant.find_one({"code": code, "is_deleted": False})

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[Tenant]:
        return await Tenant.find({"is_deleted": False}).skip(skip).limit(limit).to_list()

    async def create(self, *, obj_in: TenantCreate) -> Tenant:
        db_obj = Tenant(**obj_in.model_dump())
        await db_obj.insert()
        return db_obj

    async def update(self, *, db_obj: Tenant, obj_in: Union[TenantUpdate, Dict[str, Any]]) -> Tenant:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        await db_obj.save()
        return db_obj

    async def remove(self, *, id: UUID) -> Optional[Tenant]:
        # Soft delete mechanism
        obj = await self.get(id=id)
        if obj:
            obj.is_deleted = True
            await obj.save()
        return obj

tenant = CRUDTenant()
