import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.models.identity import User
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service handling real-time collaboration notifications and alerts."""

    async def create_notification(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        type: str = "assignment",
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        sender_id: Optional[UUID] = None,
        sender_name: Optional[str] = None,
    ) -> Notification:
        """Create and persist a notification in MongoDB."""
        try:
            notification = Notification(
                tenant_id=tenant_id,
                user_id=user_id,
                title=title,
                message=message,
                type=type,
                entity_type=entity_type,
                entity_id=entity_id,
                sender_id=sender_id,
                sender_name=sender_name,
                is_read=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await notification.insert()
            logger.info(
                f"NotificationService: Created notification '{title}' for user {user_id} (Sender: {sender_name})"
            )
            return notification
        except Exception as e:
            logger.error(f"NotificationService: Failed to create notification: {e}")
            raise

    async def get_user_notifications(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 50,
        unread_only: bool = False,
    ) -> List[Notification]:
        """Fetch notifications for a user sorted by most recent first."""
        query = {
            "tenant_id": tenant_id,
            "user_id": user_id,
        }
        if unread_only:
            query["is_read"] = False

        return await Notification.find(query).sort("-created_at").limit(limit).to_list()

    async def get_unread_count(self, *, tenant_id: UUID, user_id: UUID) -> int:
        """Count unread notifications for a user."""
        return await Notification.find({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "is_read": False,
        }).count()

    async def mark_as_read(
        self, *, tenant_id: UUID, user_id: UUID, notification_id: UUID
    ) -> bool:
        """Mark a single notification as read."""
        notification = await Notification.find_one({
            "_id": notification_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
        })
        if notification:
            notification.is_read = True
            notification.updated_at = datetime.now(timezone.utc)
            await notification.save()
            return True
        return False

    async def mark_all_as_read(self, *, tenant_id: UUID, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        result = await Notification.find({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "is_read": False,
        }).update({"$set": {"is_read": True, "updated_at": datetime.now(timezone.utc)}})
        return getattr(result, "modified_count", 0)


notification_service = NotificationService()
