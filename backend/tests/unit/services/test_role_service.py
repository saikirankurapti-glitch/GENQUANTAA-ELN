import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.rbac.role_service import RoleService
from app.schemas.rbac import RoleCreate, RoleUpdate
from app.models.rbac import Role
from app.services.rbac.exceptions import (
    RoleAlreadyExists,
    RoleNotFound,
    SystemRoleModificationError,
    SystemRoleDeletionError
)

@pytest.fixture
def role_service():
    return RoleService()

@pytest.fixture
def mock_repo():
    with patch("app.services.rbac.role_service.role_repo") as mock:
        yield mock

@pytest.mark.asyncio
async def test_create_role_success(role_service, mock_repo):
    tenant_id = uuid4()
    mock_repo.exists_by_code = AsyncMock(return_value=False)
    mock_repo.exists_by_name = AsyncMock(return_value=False)
    
    expected_role = Role(id=uuid4(), name="Test Role", code="test.role", tenant_id=tenant_id)
    mock_repo.create = AsyncMock(return_value=expected_role)
    
    obj_in = RoleCreate(name="Test Role", code="test.role", tenant_id=tenant_id)
    result = await role_service.create_role(None, obj_in=obj_in)
    
    assert result == expected_role
    mock_repo.exists_by_code.assert_called_once()
    mock_repo.exists_by_name.assert_called_once()
    mock_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_role_duplicate_code(role_service, mock_repo):
    tenant_id = uuid4()
    mock_repo.exists_by_code = AsyncMock(return_value=True) # Simulates code already exists
    
    obj_in = RoleCreate(name="Test Role", code="test.role", tenant_id=tenant_id)
    
    with pytest.raises(RoleAlreadyExists, match="already exists"):
        await role_service.create_role(None, obj_in=obj_in)

@pytest.mark.asyncio
async def test_get_role_tenant_isolation(role_service, mock_repo):
    tenant_id = uuid4()
    role_id = uuid4()
    # Simulate DB returning None for this specific tenant scoping
    mock_repo.get_by_id = AsyncMock(return_value=None)
    
    with pytest.raises(RoleNotFound):
        await role_service.get_role(None, id=role_id, tenant_id=tenant_id)

@pytest.mark.asyncio
async def test_prevent_system_role_modification(role_service, mock_repo):
    tenant_id = uuid4()
    role_id = uuid4()
    
    sys_role = Role(id=role_id, name="System Admin", code="sys.admin", tenant_id=tenant_id, is_system=True)
    mock_repo.get_by_id = AsyncMock(return_value=sys_role)
    
    obj_in = RoleUpdate(name="Hacked Admin")
    
    with pytest.raises(SystemRoleModificationError):
        await role_service.update_role(None, id=role_id, tenant_id=tenant_id, obj_in=obj_in)

@pytest.mark.asyncio
async def test_prevent_system_role_deletion(role_service, mock_repo):
    tenant_id = uuid4()
    role_id = uuid4()
    
    sys_role = Role(id=role_id, name="System Admin", code="sys.admin", tenant_id=tenant_id, is_system=True)
    mock_repo.get_by_id = AsyncMock(return_value=sys_role)
    
    with pytest.raises(SystemRoleDeletionError):
        await role_service.delete_role(None, id=role_id, tenant_id=tenant_id)
