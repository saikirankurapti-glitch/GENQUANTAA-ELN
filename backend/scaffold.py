import os

files = {
    "requirements.txt": """fastapi>=0.109.2
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.25
alembic>=1.13.1
pydantic-settings>=2.1.0
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
""",
    ".env": """PROJECT_NAME="Enterprise ELN"
API_V1_STR="/api/v1"
POSTGRES_SERVER="localhost"
POSTGRES_USER="eln_user"
POSTGRES_PASSWORD="eln_password"
POSTGRES_DB="eln_db"
POSTGRES_PORT="5432"
""",
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/db/__init__.py": "",
    "app/api/__init__.py": "",
    "app/core/config.py": """from typing import Any, Optional
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise ELN"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{info.data.get('POSTGRES_USER')}:{info.data.get('POSTGRES_PASSWORD')}@{info.data.get('POSTGRES_SERVER')}:{info.data.get('POSTGRES_PORT')}/{info.data.get('POSTGRES_DB')}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
""",
    "app/core/logging.py": """import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("eln_backend")

logger = setup_logging()
""",
    "app/core/exceptions.py": """from fastapi import Request
from fastapi.responses import JSONResponse
from .logging import logger

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
""",
    "app/db/base_class.py": """from sqlalchemy.orm import declarative_base

Base = declarative_base()
""",
    "app/db/mixins.py": """import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Boolean, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

class AuditMixin:
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
""",
    "app/db/session.py": """from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
""",
    "app/api/dependencies.py": """from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
""",
    "app/main.py": """from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import global_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Enterprise ELN API...")
    yield
    logger.info("Shutting down Enterprise ELN API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_exception_handler(Exception, global_exception_handler)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
"""
}

for path, content in files.items():
    full_path = os.path.join("d:/GENQUANTAA/ELN/backend", path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Scaffolding complete.")
