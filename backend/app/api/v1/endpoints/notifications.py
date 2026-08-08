import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.security.authorization import get_current_user, get_current_active_user
from app.models.identity import User
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


class NotificationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    title: str
    message: str
    type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None
    sender_name: Optional[str] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime


class UnreadCountResponse(BaseModel):
    unread_count: int


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    """Retrieve notifications for the authenticated user in real-time."""
    if not current_user.tenant_id:
        return []
    notifications = await notification_service.get_user_notifications(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        limit=limit,
        unread_only=unread_only,
    )
    return notifications


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
):
    """Get the current count of unread notifications for badge alerts."""
    if not current_user.tenant_id:
        return UnreadCountResponse(unread_count=0)
    count = await notification_service.get_unread_count(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Mark an individual notification as read."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant missing")
    success = await notification_service.mark_as_read(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"status": "ok", "message": "Notification marked as read"}


@router.post("/mark-all-read", response_model=dict)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read for current user."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant missing")
    count = await notification_service.mark_all_as_read(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    return {"status": "ok", "modified_count": count}
