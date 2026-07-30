import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user
from app.models.identity import User
from app.schemas.identity import (
    MFADeviceListResponse,
    MFADeviceRead,
    MFADeviceSetupRequest,
    MFADeviceSetupResponse,
    MFADeviceVerifyRequest,
)
from app.services.identity.exceptions import IdentityException, InvalidMFACode
from app.services.identity.mfa_service import mfa_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/devices", response_model=MFADeviceListResponse, summary="List MFA Devices")
async def list_mfa_devices(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """List MFA devices for current user."""
    devices = await mfa_service.mfa_device_repo.get_by_user_id(db, user_id=current_user.id)
    return MFADeviceListResponse(items=devices, total=len(devices))


@router.post("/setup", response_model=MFADeviceSetupResponse, summary="Initiate MFA Setup")
async def setup_mfa(
    *,
    db: AsyncSession = Depends(get_db),
    setup_in: MFADeviceSetupRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Setup TOTP MFA device."""
    try:
        device, qr_uri = await mfa_service.initiate_mfa_setup(
            db, user=current_user, device_name=setup_in.device_name
        )
        return MFADeviceSetupResponse(
            id=device.id, secret=device.secret, qr_code_url=qr_uri
        )
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify", response_model=MFADeviceRead, summary="Verify MFA Device")
async def verify_mfa(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: MFADeviceVerifyRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Verify 6-digit code and activate MFA."""
    try:
        return await mfa_service.verify_and_enable_mfa(
            db, user_id=current_user.id, code=verify_in.code
        )
    except InvalidMFACode as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/disable", summary="Disable MFA")
async def disable_mfa(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: MFADeviceVerifyRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Disable MFA."""
    try:
        await mfa_service.validate_user_mfa(db, user_id=current_user.id, code=verify_in.code)
        await mfa_service.disable_mfa(db, user_id=current_user.id)
        return {"message": "MFA disabled successfully."}
    except IdentityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
