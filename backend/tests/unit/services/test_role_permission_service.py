import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.rbac.role_permission_service import RolePermissionService
from app.models.rbac import Role, Permission
from app.services.rbac.exceptions import (
    RoleNotFound,
    PermissionNotFound,
    DuplicatePermissionAssignment,
    TenantIsolationError,
    ValidationError
)

@pytest.fixture
def role_perm_service():
    return RolePermissionService()

@pytest.fixture
def mock_role_repo():
    with patch("app.services.rbac.role_permission_service.role_repo") as mock:
        yield mock

@pytest.fixture
def mock_perm_repo():
    with patch("app.services.rbac.role_permission_service.permission_repo") as mock:
        yield mock

@pytest.fixture
def mock_rp_repo():
    with patch("app.services.rbac.role_permission_service.role_permission_repo") as mock:
        yield mock

@pytest.mark.asyncio
async def test_assign_permission_success(role_perm_service, mock_role_repo, mock_perm_repo, mock_rp_repo):
    tenant_id = uuid4()
    role_id = uuid4()
    perm_id = uuid4()
    
    mock_role_repo.get_by_id = AsyncMock(return_value=Role(id=role_id, tenant_id=tenant_id))
    mock_perm_repo.get_by_id = AsyncMock(return_value=Permission(id=perm_id))
    mock_rp_repo.permission_exists = AsyncMock(return_value=False)
    
    await role_perm_service.assign_permission(None, role_id=role_id, permission_id=perm_id, tenant_id=tenant_id)
    mock_rp_repo.assign_permission.assert_called_once()

@pytest.mark.asyncio
async def test_tenant_isolation_violation(role_perm_service, mock_role_repo, mock_perm_repo, mock_rp_repo):
    hacker_tenant = uuid4()
    target_role_tenant = uuid4()
    role_id = uuid4()
    
    # Role exists, but belongs to a different tenant!
    mock_role_repo.get_by_id = AsyncMock(return_value=Role(id=role_id, tenant_id=target_role_tenant))
    
    with pytest.raises(TenantIsolationError):
        await role_perm_service.assign_permission(None, role_id=role_id, permission_id=uuid4(), tenant_id=hacker_tenant)

@pytest.mark.asyncio
async def test_duplicate_assignment_prevented(role_perm_service, mock_role_repo, mock_perm_repo, mock_rp_repo):
    tenant_id = uuid4()
    role_id = uuid4()
    perm_id = uuid4()
    
    mock_role_repo.get_by_id = AsyncMock(return_value=Role(id=role_id, tenant_id=tenant_id))
    mock_perm_repo.get_by_id = AsyncMock(return_value=Permission(id=perm_id))
    mock_rp_repo.permission_exists = AsyncMock(return_value=True) # Duplicate detected
    
    with pytest.raises(DuplicatePermissionAssignment):
        await role_perm_service.assign_permission(None, role_id=role_id, permission_id=perm_id, tenant_id=tenant_id)

@pytest.mark.asyncio
async def test_bulk_assign_empty_list_rejected(role_perm_service):
    with pytest.raises(ValidationError, match="must contain at least one"):
        await role_perm_service.assign_permissions_bulk(
            None, role_id=uuid4(), permission_ids=[], tenant_id=uuid4()
        )

@pytest.mark.asyncio
async def test_bulk_assign_missing_permission(role_perm_service, mock_role_repo, mock_perm_repo):
    tenant_id = uuid4()
    role_id = uuid4()
    bad_perm_id = uuid4()
    
    mock_role_repo.get_by_id = AsyncMock(return_value=Role(id=role_id, tenant_id=tenant_id))
    mock_perm_repo.get_by_id = AsyncMock(return_value=None) # Global permission does not exist
    
    with pytest.raises(PermissionNotFound):
        await role_perm_service.assign_permissions_bulk(
            None, role_id=role_id, permission_ids=[bad_perm_id], tenant_id=tenant_id
        )
