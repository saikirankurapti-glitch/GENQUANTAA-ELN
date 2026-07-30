import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_role import role
from app.schemas.rbac import RoleCreate

@pytest.fixture
async def seeded_system_role(db: AsyncSession, system_tenant):
    """Provides a guaranteed system role seeded into the test DB."""
    obj_in = RoleCreate(name="Seeded SysAdmin", code=f"seeded.sys.{uuid4().hex[:4]}", is_system=True, tenant_id=system_tenant.id)
    return await role.create(db, obj_in=obj_in)

@pytest.fixture
async def seeded_test_role(db: AsyncSession, test_tenant):
    """Provides a standard custom role for the test tenant."""
    obj_in = RoleCreate(name="Seeded Custom Role", code=f"seeded.custom.{uuid4().hex[:4]}", tenant_id=test_tenant.id)
    return await role.create(db, obj_in=obj_in)
