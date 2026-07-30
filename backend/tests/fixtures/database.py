import asyncio
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncMock, None]:
    """Yield a mock AsyncSession for isolated test execution."""
    session = AsyncMock()
    yield session
