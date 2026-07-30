import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user, require_permission

# To test integration properly, we override FastAPI dependencies.

@pytest.fixture
async def client(db: AsyncSession, test_user) -> AsyncClient:
    """
    Returns an authenticated AsyncClient with all permissions granted.
    Overrides `get_db` to use the transactional test database,
    and overrides authorization to yield the test_user.
    """
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    
    # We must globally override require_permission to simply return the user, bypassing SQL checks
    # since we are specifically testing endpoint integration logic, not the auth layer SQL.
    # If full end-to-end auth SQL tests are desired, we'd seed the DB and not override this.
    def mock_require_permission(permission_code: str):
        def dependency():
            return test_user
        return dependency
        
    app.dependency_overrides[require_permission] = mock_require_permission

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture
async def unauthorized_client(db: AsyncSession) -> AsyncClient:
    """Returns a client with no authentication (No JWT provided)."""
    app.dependency_overrides[get_db] = lambda: db
    # We leave auth dependencies intact, which will inherently throw 401 Unauthorized
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def forbidden_client(db: AsyncSession, test_user) -> AsyncClient:
    """Returns an authenticated client, but hardcodes permission dependency to fail (403)."""
    from fastapi import HTTPException, status
    
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    
    def mock_require_permission(permission_code: str):
        def dependency():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return dependency
        
    app.dependency_overrides[require_permission] = mock_require_permission

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
