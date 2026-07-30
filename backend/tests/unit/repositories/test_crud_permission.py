import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_permission import permission
from app.schemas.rbac import PermissionCreate, PermissionUpdate

@pytest.mark.asyncio
async def test_create_permission(db: AsyncSession):
    code = f"test.res.act_{uuid4().hex[:6]}"
    obj_in = PermissionCreate(module="test", resource="res", action="act", code=code)
    db_obj = await permission.create(db, obj_in=obj_in)
    
    assert db_obj.id is not None
    assert db_obj.code == code
    assert db_obj.module == "test"

@pytest.mark.asyncio
async def test_update_permission(db: AsyncSession):
    code = f"update.res.act_{uuid4().hex[:6]}"
    obj_in = PermissionCreate(module="update", resource="res", action="act", code=code)
    db_obj = await permission.create(db, obj_in=obj_in)
    
    update_in = PermissionUpdate(description="New Description")
    updated_obj = await permission.update(db, db_obj=db_obj, obj_in=update_in)
    
    assert updated_obj.description == "New Description"

@pytest.mark.asyncio
async def test_hard_delete_permission(db: AsyncSession):
    code = f"delete.res.act_{uuid4().hex[:6]}"
    obj_in = PermissionCreate(module="delete", resource="res", action="act", code=code)
    db_obj = await permission.create(db, obj_in=obj_in)
    
    deleted_obj = await permission.delete(db, id=db_obj.id)
    assert deleted_obj is not None
    
    fetched = await permission.get_by_id(db, id=db_obj.id)
    assert fetched is None

@pytest.mark.asyncio
async def test_search_permissions(db: AsyncSession):
    mod = f"mod_{uuid4().hex[:6]}"
    for i in range(3):
        await permission.create(db, obj_in=PermissionCreate(
            module=mod, resource=f"res{i}", action="act", code=f"{mod}.res{i}.act"
        ))
        
    items, total = await permission.search(db, query=mod, page=1, page_size=10)
    assert total >= 3
    assert len(items) >= 3
    assert items[0].module == mod
