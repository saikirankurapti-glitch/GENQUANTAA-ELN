import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_permission_success(client: AsyncClient):
    code = f"test.res.act_{uuid4().hex[:6]}"
    payload = {
        "module": "test",
        "resource": "res",
        "action": f"act_{uuid4().hex[:6]}",
        "code": code,
        "description": "API Test Perm"
    }
    response = await client.post("/api/v1/permissions/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == code
    assert "id" in data

@pytest.mark.asyncio
async def test_create_permission_malformed(client: AsyncClient):
    payload = {
        "module": "test",
        "resource": "res",
        "action": "act",
        "code": "wrong_format_entirely",
        "description": "API Test Perm"
    }
    response = await client.post("/api/v1/permissions/", json=payload)
    # The code doesn't match module.resource.action
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_create_permission_duplicate(client: AsyncClient):
    code = f"dup.res.act_{uuid4().hex[:6]}"
    payload = {"module": "dup", "resource": "res", "action": f"act_{uuid4().hex[:6]}", "code": code}
    
    await client.post("/api/v1/permissions/", json=payload)
    response = await client.post("/api/v1/permissions/", json=payload)
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_permission_success(client: AsyncClient):
    code = f"get.res.act_{uuid4().hex[:6]}"
    payload = {"module": "get", "resource": "res", "action": f"act_{uuid4().hex[:6]}", "code": code}
    
    create_resp = await client.post("/api/v1/permissions/", json=payload)
    perm_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/v1/permissions/{perm_id}")
    assert response.status_code == 200
    assert response.json()["id"] == perm_id

@pytest.mark.asyncio
async def test_get_permission_not_found(client: AsyncClient):
    response = await client.get(f"/api/v1/permissions/{uuid4()}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_search_permissions(client: AsyncClient):
    term = uuid4().hex[:6]
    code = f"search.{term}.act"
    payload = {"module": "search", "resource": term, "action": "act", "code": code}
    await client.post("/api/v1/permissions/", json=payload)
    
    response = await client.get(f"/api/v1/permissions/search?query={term}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(term in p["code"] for p in data["items"])

@pytest.mark.asyncio
async def test_auth_blocks_permissions(unauthorized_client: AsyncClient, forbidden_client: AsyncClient):
    resp1 = await unauthorized_client.get("/api/v1/permissions/")
    assert resp1.status_code == 401
    
    resp2 = await forbidden_client.get("/api/v1/permissions/")
    assert resp2.status_code == 403
