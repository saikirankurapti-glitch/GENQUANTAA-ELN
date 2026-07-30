import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.identity import UserCreate
from app.services.identity.exceptions import UserNotFound
from app.services.identity.user_service import user_service


@pytest.mark.asyncio
async def test_tenant_isolation_user_lookup(db: AsyncSession):
    """Security test: Ensure User in Tenant A cannot be fetched using Tenant B scope."""
    tenant_a = Tenant(id=uuid.uuid4(), name="Tenant A", code=f"ta_{uuid.uuid4().hex[:6]}")
    tenant_b = Tenant(id=uuid.uuid4(), name="Tenant B", code=f"tb_{uuid.uuid4().hex[:6]}")
    db.add_all([tenant_a, tenant_b])
    await db.commit()

    user_in = UserCreate(
        username="tenant_a_user",
        email="usera@tenanta.com",
        first_name="User",
        last_name="A",
        password="ValidPassword123!",
        tenant_id=tenant_a.id,
    )
    user_a = await user_service.register_user(db, obj_in=user_in)

    # Fetch using Tenant A scope -> Success
    found_user = await user_service.get_user_by_id(db, id=user_a.id, tenant_id=tenant_a.id)
    assert found_user.id == user_a.id

    # Fetch using Tenant B scope -> Raises UserNotFound
    with pytest.raises(UserNotFound):
        await user_service.get_user_by_id(db, id=user_a.id, tenant_id=tenant_b.id)
