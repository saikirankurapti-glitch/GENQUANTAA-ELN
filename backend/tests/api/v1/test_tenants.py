import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_tenant(client: AsyncClient) -> None:
    data = {"name": "Test Tenant", "code": "TEST1"}
    response = await client.post("/api/v1/tenants/", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["code"] == data["code"]
    assert "id" in content

@pytest.mark.asyncio
async def test_read_tenants(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tenants/")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)
