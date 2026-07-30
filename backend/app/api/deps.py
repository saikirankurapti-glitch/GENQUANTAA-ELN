from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

try:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
except Exception:
    try:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", pool_pre_ping=True)
    except Exception:
        # Mock engine fallback for offline module import
        engine = None

if engine is not None:
    AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)
else:
    AsyncSessionLocal = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to yield an async database session per request.
    """
    if AsyncSessionLocal:
        async with AsyncSessionLocal() as session:
            yield session
    else:
        yield None
