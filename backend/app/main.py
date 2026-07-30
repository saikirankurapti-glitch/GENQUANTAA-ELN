from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title="Enterprise AI-Powered ELN API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API for the Electronic Laboratory Notebook",
    version="1.0.0",
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
