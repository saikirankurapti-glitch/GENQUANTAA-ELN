import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user
from app.models.identity import User
from app.schemas.identity import TrustedDeviceListResponse, TrustedDeviceRead
from app.services.identity.trusted_device_service import trusted_device_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=TrustedDeviceListResponse, summary="List Trusted Devices")
async def list_trusted_devices(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """List registered trusted devices for current user."""
    devices = await trusted_device_service.list_trusted_devices(db, user_id=current_user.id)
    return TrustedDeviceListResponse(items=devices, total=len(devices))


@router.post("/", response_model=TrustedDeviceRead, status_code=status.HTTP_201_CREATED, summary="Register Trusted Device")
async def register_trusted_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_identifier: str,
    device_name: str = "Client Device",
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Register client device as trusted."""
    device = await trusted_device_service.register_trusted_device(
        db, user_id=current_user.id, device_identifier=device_identifier, device_name=device_name
    )
    return device


@router.delete("/{device_id}", summary="Remove Trusted Device")
async def remove_trusted_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: UUID,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Remove a trusted device."""
    device = await trusted_device_service.trusted_device_repo.get_by_device_identifier(
        db, user_id=current_user.id, device_identifier=str(device_id)
    )
    if device:
        await db.delete(device)
        await db.commit()
        return {"message": "Trusted device removed."}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trusted device not found.")
