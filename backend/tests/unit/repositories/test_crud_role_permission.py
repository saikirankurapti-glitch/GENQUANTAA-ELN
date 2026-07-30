import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_role import role
from app.crud.crud_permission import permission
from app.crud.crud_role_permission import role_permission
from app.schemas.rbac import RoleCreate, PermissionCreate

@pytest.mark.asyncio
async def test_assign_permission(db: AsyncSession):
    tenant_id = uuid4()
    r = await role.create(db, obj_in=RoleCreate(name="R1", code=f"r1_{uuid4().hex}", tenant_id=tenant_id))
    p = await permission.create(db, obj_in=PermissionCreate(module="m", resource="r", action="a", code=f"m.r.a_{uuid4().hex}"))
    
    rp = await role_permission.assign_permission(db, role_id=r.id, permission_id=p.id)
    assert rp is not None
    
    exists = await role_permission.permission_exists(db, role_id=r.id, permission_id=p.id)
    assert exists is True

@pytest.mark.asyncio
async def test_assign_permissions_bulk_and_duplicate_prevention(db: AsyncSession):
    tenant_id = uuid4()
    r = await role.create(db, obj_in=RoleCreate(name="R2", code=f"r2_{uuid4().hex}", tenant_id=tenant_id))
    p1 = await permission.create(db, obj_in=PermissionCreate(module="m", resource="r", action="a1", code=f"m.r.a1_{uuid4().hex}"))
    p2 = await permission.create(db, obj_in=PermissionCreate(module="m", resource="r", action="a2", code=f"m.r.a2_{uuid4().hex}"))
    
    # Bulk assign
    count = await role_permission.assign_permissions_bulk(db, role_id=r.id, permission_ids=[p1.id, p2.id])
    assert count == 2
    
    # Duplicate bulk assign
    count_dup = await role_permission.assign_permissions_bulk(db, role_id=r.id, permission_ids=[p1.id, p2.id])
    assert count_dup == 0  # Should skip existing safely

@pytest.mark.asyncio
async def test_remove_permissions_bulk(db: AsyncSession):
    tenant_id = uuid4()
    r = await role.create(db, obj_in=RoleCreate(name="R3", code=f"r3_{uuid4().hex}", tenant_id=tenant_id))
    p1 = await permission.create(db, obj_in=PermissionCreate(module="m", resource="r", action="a1", code=f"m.r.a1_{uuid4().hex}"))
    
    await role_permission.assign_permissions_bulk(db, role_id=r.id, permission_ids=[p1.id])
    
    # Remove
    count = await role_permission.remove_permissions_bulk(db, role_id=r.id, permission_ids=[p1.id])
    assert count == 1
    
    # Check
    exists = await role_permission.permission_exists(db, role_id=r.id, permission_id=p1.id)
    assert exists is False

@pytest.mark.asyncio
async def test_replace_permissions(db: AsyncSession):
    tenant_id = uuid4()
    r = await role.create(db, obj_in=RoleCreate(name="R4", code=f"r4_{uuid4().hex}", tenant_id=tenant_id))
    p1 = await permission.create(db, obj_in=PermissionCreate(module="m", resource="r", action="a1", code=f"m.r.a1_{uuid4().hex}"))
    p2 = await permission.create(db, obj_in=PermissionCreate(module="m", resource="r", action="a2", code=f"m.r.a2_{uuid4().hex}"))
    
    # Assign p1
    await role_permission.assign_permission(db, role_id=r.id, permission_id=p1.id)
    
    # Replace with p2
    await role_permission.replace_permissions(db, role_id=r.id, permission_ids=[p2.id])
    
    # p1 should be gone, p2 should exist
    assert await role_permission.permission_exists(db, role_id=r.id, permission_id=p1.id) is False
    assert await role_permission.permission_exists(db, role_id=r.id, permission_id=p2.id) is True
