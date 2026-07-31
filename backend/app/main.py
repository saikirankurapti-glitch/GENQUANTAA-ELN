from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.api.v1.api import api_router
from app.models.tenant import Tenant
from app.models.identity import (
    User, UserProfile, UserRole, UserPreference, RefreshToken,
    UserSession, ApiKey, MFADevice, TrustedDevice, ElectronicSignatureProfile,
    LoginHistory, PasswordHistory
)
from app.models.rbac import Role, Permission, RolePermission

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Initialize Beanie with our document models
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            Tenant,
            User, UserProfile, UserRole, UserPreference, RefreshToken,
            UserSession, ApiKey, MFADevice, TrustedDevice, ElectronicSignatureProfile,
            LoginHistory, PasswordHistory,
            Role, Permission, RolePermission
        ]
    )
    yield
    client.close()

app = FastAPI(
    title="Enterprise AI-Powered ELN API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API for the Electronic Laboratory Notebook",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
