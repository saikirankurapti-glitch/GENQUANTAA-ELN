import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user
from app.models.identity import User
from app.schemas.identity import UserSessionListResponse, UserSessionRead
from app.services.identity.exceptions import SessionNotFound
from app.services.identity.session_service import session_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=UserSessionListResponse, summary="List Active Sessions")
async def list_active_sessions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """List all active browser/device sessions for current user."""
    sessions = await session_service.list_active_sessions(db, user_id=current_user.id)
    return UserSessionListResponse(items=sessions, total=len(sessions))


@router.delete("/current", summary="Revoke Current Session")
async def revoke_current_session(
    *,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(..., description="Bearer session_token"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Revoke active session token."""
    raw_token = authorization.replace("Bearer ", "").strip()
    try:
        session = await session_service.validate_session(db, raw_session_token=raw_token)
        await session_service.revoke_session(db, session_id=session.id)
        return {"message": "Current session revoked successfully."}
    except SessionNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{session_id}", summary="Revoke Specific Session")
async def revoke_session(
    *,
    db: AsyncSession = Depends(get_db),
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Revoke a specific session by ID."""
    revoked = await session_service.revoke_session(db, session_id=session_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return {"message": f"Session {session_id} revoked successfully."}


@router.delete("/", summary="Revoke All Sessions")
async def revoke_all_sessions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Revoke all active sessions for current user."""
    count = await session_service.revoke_all_user_sessions(db, user_id=current_user.id)
    return {"message": f"Revoked {count} active sessions."}
