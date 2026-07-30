import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_role import role
from app.schemas.rbac import RoleCreate, RoleUpdate
from app.db.enums import RoleStatus

@pytest.mark.asyncio
async def test_create_role(db: AsyncSession):
    tenant_id = uuid4()
    obj_in = RoleCreate(name="Test Admin", code="test.admin", description="Test role", tenant_id=tenant_id)
    db_obj = await role.create(db, obj_in=obj_in)
    
    assert db_obj.id is not None
    assert db_obj.name == "Test Admin"
    assert db_obj.code == "test.admin"
    assert db_obj.tenant_id == tenant_id
    assert db_obj.is_system is False

@pytest.mark.asyncio
async def test_update_role(db: AsyncSession):
    tenant_id = uuid4()
    obj_in = RoleCreate(name="Manager", code="mgr", tenant_id=tenant_id)
    db_obj = await role.create(db, obj_in=obj_in)
    
    update_in = RoleUpdate(name="Super Manager")
    updated_obj = await role.update(db, db_obj=db_obj, obj_in=update_in)
    
    assert updated_obj.name == "Super Manager"
    assert updated_obj.code == "mgr"

@pytest.mark.asyncio
async def test_soft_delete_role(db: AsyncSession):
    tenant_id = uuid4()
    obj_in = RoleCreate(name="To Delete", code="delete.me", tenant_id=tenant_id)
    db_obj = await role.create(db, obj_in=obj_in)
    
    deleted_obj = await role.soft_delete(db, id=db_obj.id)
    assert deleted_obj is not None
    assert deleted_obj.is_deleted is True
    assert deleted_obj.deleted_at is not None
    
    # Verify it doesn't show up in normal gets (soft delete check)
    fetched = await role.get_by_id(db, id=db_obj.id, tenant_id=tenant_id)
    assert fetched is None

@pytest.mark.asyncio
async def test_search_and_pagination(db: AsyncSession):
    tenant_id = uuid4()
    # Create 5 roles
    for i in range(5):
        await role.create(db, obj_in=RoleCreate(name=f"SearchRole {i}", code=f"search.code.{i}", tenant_id=tenant_id))
        
    # Search for them
    items, total = await role.search(db, tenant_id=tenant_id, query="SearchRole", page=1, page_size=2)
    
    assert total >= 5
    assert len(items) == 2
    assert "SearchRole" in items[0].name

@pytest.mark.asyncio
async def test_exists_checks(db: AsyncSession):
    tenant_id = uuid4()
    code = f"unique.code.{uuid4().hex[:6]}"
    obj_in = RoleCreate(name="Unique Role", code=code, tenant_id=tenant_id)
    await role.create(db, obj_in=obj_in)
    
    assert await role.exists_by_code(db, code=code, tenant_id=tenant_id) is True
    assert await role.exists_by_code(db, code="nonexistent", tenant_id=tenant_id) is False
