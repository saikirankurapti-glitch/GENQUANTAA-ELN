import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_permission import permission
from app.schemas.rbac import PermissionCreate

@pytest.fixture
async def seeded_permission_1(db: AsyncSession):
    """Provides a seeded valid permission."""
    obj_in = PermissionCreate(module="test", resource="module", action="read", code=f"test.module.read_{uuid4().hex[:4]}")
    return await permission.create(db, obj_in=obj_in)

@pytest.fixture
async def seeded_permission_2(db: AsyncSession):
    """Provides a second seeded valid permission."""
    obj_in = PermissionCreate(module="test", resource="module", action="write", code=f"test.module.write_{uuid4().hex[:4]}")
    return await permission.create(db, obj_in=obj_in)
