import pytest
from httpx import AsyncClient
from uuid import uuid4

async def setup_role_and_permission(client: AsyncClient, test_tenant):
    """Helper to create a fresh role and permission for integration tests."""
    r_payload = {"name": f"RP_Role_{uuid4().hex[:6]}", "code": f"rp.role.{uuid4().hex[:6]}", "tenant_id": str(test_tenant.id)}
    r_resp = await client.post("/api/v1/roles/", json=r_payload)
    role_id = r_resp.json()["id"]
    
    p_code = f"mod.res.act_{uuid4().hex[:6]}"
    p_payload = {"module": "mod", "resource": "res", "action": f"act_{uuid4().hex[:6]}", "code": p_code}
    p_resp = await client.post("/api/v1/permissions/", json=p_payload)
    perm_id = p_resp.json()["id"]
    
    return role_id, perm_id

@pytest.mark.asyncio
async def test_assign_permission(client: AsyncClient, test_tenant):
    role_id, perm_id = await setup_role_and_permission(client, test_tenant)
    
    payload = {"permission_ids": [perm_id]}
    response = await client.post(f"/api/v1/roles/{role_id}/permissions", json=payload)
    
    assert response.status_code == 201
    assert "successfully" in response.json()["detail"]

@pytest.mark.asyncio
async def test_assign_duplicate_permission_409(client: AsyncClient, test_tenant):
    role_id, perm_id = await setup_role_and_permission(client, test_tenant)
    payload = {"permission_ids": [perm_id]}
    
    # First assign
    await client.post(f"/api/v1/roles/{role_id}/permissions", json=payload)
    # Second assign exact same single permission
    response = await client.post(f"/api/v1/roles/{role_id}/permissions", json=payload)
    
    assert response.status_code == 409
    assert "already assigned" in response.json()["detail"]

@pytest.mark.asyncio
async def test_remove_permission(client: AsyncClient, test_tenant):
    role_id, perm_id = await setup_role_and_permission(client, test_tenant)
    await client.post(f"/api/v1/roles/{role_id}/permissions", json={"permission_ids": [perm_id]})
    
    # Verify it exists
    get_resp = await client.get(f"/api/v1/roles/{role_id}/permissions")
    assert any(p["id"] == perm_id for p in get_resp.json())
    
    # Remove
    del_resp = await client.delete(f"/api/v1/roles/{role_id}/permissions/{perm_id}")
    assert del_resp.status_code == 200
    
    # Verify it's gone
    get_resp2 = await client.get(f"/api/v1/roles/{role_id}/permissions")
    assert not any(p["id"] == perm_id for p in get_resp2.json())

@pytest.mark.asyncio
async def test_replace_permissions(client: AsyncClient, test_tenant):
    role_id, perm1_id = await setup_role_and_permission(client, test_tenant)
    _, perm2_id = await setup_role_and_permission(client, test_tenant)
    
    # Assign perm 1
    await client.post(f"/api/v1/roles/{role_id}/permissions", json={"permission_ids": [perm1_id]})
    
    # Replace with perm 2
    response = await client.put(f"/api/v1/roles/{role_id}/permissions", json={"permission_ids": [perm2_id]})
    assert response.status_code == 200
    
    # Verify only perm 2 exists
    get_resp = await client.get(f"/api/v1/roles/{role_id}/permissions")
    ids = [p["id"] for p in get_resp.json()]
    assert perm2_id in ids
    assert perm1_id not in ids

@pytest.mark.asyncio
async def test_invalid_uuid_payload(client: AsyncClient):
    payload = {"permission_ids": ["not-a-uuid"]}
    # Pydantic should catch this immediately as HTTP 422 Unprocessable Entity
    response = await client.post(f"/api/v1/roles/{uuid4()}/permissions", json=payload)
    assert response.status_code == 422
