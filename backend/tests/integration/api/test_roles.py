import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_role_success(client: AsyncClient, test_tenant):
    payload = {
        "name": "API Role",
        "code": f"api.role.{uuid4().hex[:6]}",
        "description": "Integration testing",
        "tenant_id": str(test_tenant.id)
    }
    response = await client.post("/api/v1/roles/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["code"] == payload["code"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_role_duplicate_conflict(client: AsyncClient, test_tenant):
    code = f"dup.role.{uuid4().hex[:6]}"
    payload = {"name": "Dup Role", "code": code, "tenant_id": str(test_tenant.id)}
    
    # Create first time
    await client.post("/api/v1/roles/", json=payload)
    
    # Second time should fail
    response = await client.post("/api/v1/roles/", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_role_success(client: AsyncClient, test_tenant):
    payload = {"name": "Get Role", "code": f"get.role.{uuid4().hex[:6]}", "tenant_id": str(test_tenant.id)}
    create_resp = await client.post("/api/v1/roles/", json=payload)
    role_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/v1/roles/{role_id}")
    assert response.status_code == 200
    assert response.json()["id"] == role_id

@pytest.mark.asyncio
async def test_update_role_success(client: AsyncClient, test_tenant):
    payload = {"name": "Update Role", "code": f"upd.role.{uuid4().hex[:6]}", "tenant_id": str(test_tenant.id)}
    create_resp = await client.post("/api/v1/roles/", json=payload)
    role_id = create_resp.json()["id"]
    
    update_payload = {"name": "Updated API Role"}
    response = await client.put(f"/api/v1/roles/{role_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated API Role"

@pytest.mark.asyncio
async def test_delete_role_success(client: AsyncClient, test_tenant):
    payload = {"name": "Delete Role", "code": f"del.role.{uuid4().hex[:6]}", "tenant_id": str(test_tenant.id)}
    create_resp = await client.post("/api/v1/roles/", json=payload)
    role_id = create_resp.json()["id"]
    
    response = await client.delete(f"/api/v1/roles/{role_id}")
    assert response.status_code == 200
    
    # Verify it is gone
    get_resp = await client.get(f"/api/v1/roles/{role_id}")
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_search_roles(client: AsyncClient, test_tenant):
    term = uuid4().hex[:8]
    payload = {"name": f"Searchable {term}", "code": f"search.{term}", "tenant_id": str(test_tenant.id)}
    await client.post("/api/v1/roles/", json=payload)
    
    response = await client.get(f"/api/v1/roles/search?query={term}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(term in r["name"] for r in data["items"])

@pytest.mark.asyncio
async def test_unauthorized_and_forbidden(unauthorized_client: AsyncClient, forbidden_client: AsyncClient, test_tenant):
    payload = {"name": "Auth Role", "code": f"auth.role.{uuid4().hex[:6]}", "tenant_id": str(test_tenant.id)}
    
    # Missing JWT
    resp1 = await unauthorized_client.post("/api/v1/roles/", json=payload)
    assert resp1.status_code == 401
    
    # Valid JWT but missing the "rbac.role.create" permission
    resp2 = await forbidden_client.post("/api/v1/roles/", json=payload)
    assert resp2.status_code == 403

@pytest.mark.asyncio
async def test_tenant_isolation_violation(client: AsyncClient):
    # Try to create a role in a completely random tenant UUID
    hacker_tenant_id = str(uuid4())
    payload = {"name": "Hacker Role", "code": "hacker.role", "tenant_id": hacker_tenant_id}
    
    response = await client.post("/api/v1/roles/", json=payload)
    assert response.status_code == 403
    assert "Cannot create roles outside of your assigned tenant" in response.json()["detail"]
