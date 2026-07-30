import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.identity import User

@pytest.fixture
def system_admin_user(system_tenant) -> User:
    """Returns a mock System Administrator user."""
    return User(id=uuid4(), tenant_id=system_tenant.id, status="active", username="sysadmin")

@pytest.fixture
def test_user(test_tenant) -> User:
    """Returns a standard active user for Organization A."""
    return User(id=uuid4(), tenant_id=test_tenant.id, status="active", username="testuser")

@pytest.fixture
def unauthorized_user(test_tenant) -> User:
    """Returns a user without proper RBAC privileges."""
    return User(id=uuid4(), tenant_id=test_tenant.id, status="active", username="hacker")

@pytest.fixture
def inactive_user(test_tenant) -> User:
    """Returns a user that has been deactivated."""
    return User(id=uuid4(), tenant_id=test_tenant.id, status="inactive", username="fired_user")
