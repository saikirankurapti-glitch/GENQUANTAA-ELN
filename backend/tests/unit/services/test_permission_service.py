import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.rbac.permission_service import PermissionService
from app.schemas.rbac import PermissionCreate, PermissionUpdate
from app.models.rbac import Permission
from app.services.rbac.exceptions import (
    PermissionAlreadyExists,
    PermissionNotFound,
    InvalidPermissionCode,
    ValidationError
)

@pytest.fixture
def permission_service():
    return PermissionService()

@pytest.fixture
def mock_repo():
    with patch("app.services.rbac.permission_service.permission_repo") as mock:
        yield mock

@pytest.mark.asyncio
async def test_permission_format_validation(permission_service, mock_repo):
    mock_repo.exists = AsyncMock(return_value=False)
    
    # Missing action
    with pytest.raises(ValidationError):
        await permission_service.create_permission(
            None, 
            obj_in=PermissionCreate(module="mod", resource="res", action="", code="mod.res.act")
        )

    # Malformed code structure
    with pytest.raises(InvalidPermissionCode):
        await permission_service.create_permission(
            None, 
            obj_in=PermissionCreate(module="mod", resource="res", action="act", code="mod.res_wrong")
        )

@pytest.mark.asyncio
async def test_create_permission_normalization(permission_service, mock_repo):
    mock_repo.exists = AsyncMock(return_value=False)
    expected_perm = Permission(id=uuid4(), code="mod.res.act")
    mock_repo.create = AsyncMock(return_value=expected_perm)
    
    # Messy casing and whitespace
    obj_in = PermissionCreate(module=" Mod ", resource="RES", action="Act", code="mod.res.act")
    result = await permission_service.create_permission(None, obj_in=obj_in)
    
    assert obj_in.module == "mod"
    assert obj_in.resource == "res"
    assert obj_in.action == "act"
    assert result == expected_perm

@pytest.mark.asyncio
async def test_duplicate_permission_detection(permission_service, mock_repo):
    mock_repo.exists = AsyncMock(return_value=True) # Force duplicate detection
    
    obj_in = PermissionCreate(module="mod", resource="res", action="act", code="mod.res.act")
    
    with pytest.raises(PermissionAlreadyExists):
        await permission_service.create_permission(None, obj_in=obj_in)

@pytest.mark.asyncio
async def test_permission_not_found(permission_service, mock_repo):
    mock_repo.get_by_id = AsyncMock(return_value=None)
    
    with pytest.raises(PermissionNotFound):
        await permission_service.get_permission(None, id=uuid4())

@pytest.mark.asyncio
async def test_update_permission_revalidates_code(permission_service, mock_repo):
    perm_id = uuid4()
    existing_perm = Permission(id=perm_id, module="mod", resource="res", action="act", code="mod.res.act")
    mock_repo.get_by_id = AsyncMock(return_value=existing_perm)
    mock_repo.exists = AsyncMock(return_value=False)
    mock_repo.update = AsyncMock(return_value=existing_perm)
    
    # Trying to change action but keeping old code should trigger format validation exception
    obj_in = PermissionUpdate(action="delete")
    
    with pytest.raises(InvalidPermissionCode):
        await permission_service.update_permission(None, id=perm_id, obj_in=obj_in)
