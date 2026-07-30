import logging
from typing import Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user, get_current_tenant
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.identity import (
    ElectronicSignatureProfileCreate,
    ElectronicSignatureProfileRead,
    ElectronicSignatureProfileUpdate,
)
from app.services.identity.electronic_signature_service import electronic_signature_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SignatureVerifyRequest(BaseModel):
    password: str = Field(..., description="User password for dual-factor verification")
    signature_meaning: str = Field(..., description="Legal sign-off intent (e.g., 'Author', 'Reviewer', 'Approver')")


@router.post("/profile", response_model=ElectronicSignatureProfileRead, summary="Setup Signature Profile")
async def create_signature_profile(
    *,
    db: AsyncSession = Depends(get_db),
    profile_in: ElectronicSignatureProfileCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Setup electronic signature profile for current user."""
    return await electronic_signature_service.setup_signature_profile(
        db, user_id=current_user.id, obj_in=profile_in
    )


@router.put("/profile", response_model=ElectronicSignatureProfileRead, summary="Update Signature Profile")
async def update_signature_profile(
    *,
    db: AsyncSession = Depends(get_db),
    profile_in: ElectronicSignatureProfileUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update electronic signature profile."""
    return await electronic_signature_service.setup_signature_profile(
        db, user_id=current_user.id, obj_in=profile_in
    )


@router.post("/verify", summary="Verify Electronic Signature Intent")
async def verify_signature(
    *,
    db: AsyncSession = Depends(get_db),
    verify_in: SignatureVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """FDA 21 CFR Part 11 Dual-Factor Signature Re-authentication."""
    is_valid = await electronic_signature_service.verify_signature_intent(
        db,
        user_id=current_user.id,
        tenant_id=current_tenant.id,
        password=verify_in.password,
        signature_meaning=verify_in.signature_meaning,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Electronic signature re-authentication failed. Incorrect credentials or disabled profile.",
        )
    return {"message": "Electronic signature verified successfully."}
