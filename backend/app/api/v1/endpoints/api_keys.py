import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.identity import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    ApiKeyRead,
)
from app.services.identity.api_key_service import api_key_service
from app.services.identity.exceptions import ApiKeyNotFound

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED, summary="Create API Key")
async def create_api_key(
    *,
    db: AsyncSession = Depends(get_db),
    key_in: ApiKeyCreate,
    current_user: User = Depends(require_permission("identity.apikey.create")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Generate a new API key (Secret returned ONLY ONCE in response)."""
    api_key_obj, raw_key = await api_key_service.create_api_key(
        db,
        tenant_id=current_tenant.id,
        user_id=current_user.id,
        name=key_in.name,
        expires_at=key_in.expires_at,
    )
    return ApiKeyCreateResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        api_key=raw_key,
        expires_at=api_key_obj.expires_at,
        created_at=api_key_obj.created_at,
    )


@router.get("/", response_model=ApiKeyListResponse, summary="List API Keys")
async def list_api_keys(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("identity.apikey.read")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """List all API keys for current user."""
    keys = await api_key_service.list_user_api_keys(
        db, user_id=current_user.id, tenant_id=current_tenant.id
    )
    return ApiKeyListResponse(items=keys, total=len(keys))


@router.post("/{key_id}/rotate", response_model=ApiKeyCreateResponse, summary="Rotate API Key")
async def rotate_api_key(
    *,
    db: AsyncSession = Depends(get_db),
    key_id: UUID,
    current_user: User = Depends(require_permission("identity.apikey.create")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Revoke an existing API key and issue a new replacement key."""
    try:
        existing = await api_key_service.api_key_repo.get_by_id(
            db, id=key_id, tenant_id=current_tenant.id
        )
        if not existing:
            raise ApiKeyNotFound(f"API Key {key_id} not found.")

        # Deactivate old
        await api_key_service.revoke_api_key(db, id=key_id, tenant_id=current_tenant.id)

        # Issue new
        new_key_obj, raw_key = await api_key_service.create_api_key(
            db,
            tenant_id=current_tenant.id,
            user_id=current_user.id,
            name=f"{existing.name} (Rotated)",
            expires_at=existing.expires_at,
        )
        return ApiKeyCreateResponse(
            id=new_key_obj.id,
            name=new_key_obj.name,
            api_key=raw_key,
            expires_at=new_key_obj.expires_at,
            created_at=new_key_obj.created_at,
        )
    except ApiKeyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{key_id}", summary="Revoke API Key")
async def revoke_api_key(
    *,
    db: AsyncSession = Depends(get_db),
    key_id: UUID,
    current_user: User = Depends(require_permission("identity.apikey.delete")),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Deactivate an API Key."""
    try:
        await api_key_service.revoke_api_key(db, id=key_id, tenant_id=current_tenant.id)
        return {"message": "API key revoked successfully."}
    except ApiKeyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
