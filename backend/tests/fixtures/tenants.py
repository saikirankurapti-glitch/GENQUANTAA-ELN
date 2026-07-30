import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.crud.crud_tenant import tenant as tenant_repo
from app.schemas.tenant import TenantCreate

@pytest.fixture
async def system_tenant(db: AsyncSession) -> Tenant:
    """Provides the overarching SYSTEM tenant."""
    code = "SYSTEM"
    existing = await tenant_repo.get_by_code(db, code=code)
    if existing: return existing
    
    tenant_in = TenantCreate(name="System", code=code, description="System Tenant")
    return await tenant_repo.create(db, obj_in=tenant_in)

@pytest.fixture
async def test_tenant(db: AsyncSession) -> Tenant:
    """Provides Organization A (default working tenant)."""
    code = f"org_a_{uuid4().hex[:4]}"
    tenant_in = TenantCreate(name="Organization A", code=code, description="Test Tenant A")
    return await tenant_repo.create(db, obj_in=tenant_in)

@pytest.fixture
async def tenant_b(db: AsyncSession) -> Tenant:
    """Provides Organization B for cross-tenant isolation testing."""
    code = f"org_b_{uuid4().hex[:4]}"
    tenant_in = TenantCreate(name="Organization B", code=code, description="Test Tenant B")
    return await tenant_repo.create(db, obj_in=tenant_in)
