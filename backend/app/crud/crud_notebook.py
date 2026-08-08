import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from uuid import UUID

from app.models.notebook import (
    NotebookAttachment,
    NotebookComment,
    NotebookEntry,
    NotebookEntryVersion,
    NotebookTag,
)
from app.schemas.notebook import (
    NotebookEntryCreate,
    NotebookEntryUpdate,
    NotebookFilter,
    NotebookPagination,
)

logger = logging.getLogger(__name__)


class NotebookRepository:
    """Async Repository handling data access for Notebook Entry and Version records with tenant isolation."""

    async def create_entry(
        self,
        *,
        obj_in: NotebookEntryCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> NotebookEntry:
        """Create a new NotebookEntry and its initial NotebookEntryVersion (version 1)."""
        entry = NotebookEntry(
            tenant_id=tenant_id,
            experiment_id=obj_in.experiment_id,
            author_id=current_user_id,
            title=obj_in.title,
            content=obj_in.content,
            entry_type=obj_in.entry_type,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await entry.insert()

        # Create initial Version 1 snapshot
        initial_version = NotebookEntryVersion(
            entry_id=entry.id,
            version=1,
            title=entry.title,
            content=entry.content,
            created_at=datetime.now(timezone.utc),
        )
        await initial_version.insert()
        return entry

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[NotebookEntry]:
        """Fetch NotebookEntry by ID within tenant scope."""
        entry = await NotebookEntry.find_one(
            NotebookEntry.id == id,
            NotebookEntry.tenant_id == tenant_id,
            NotebookEntry.is_deleted == False
        )
        return entry

    async def update_entry(
        self,
        *,
        db_obj: NotebookEntry,
        obj_in: NotebookEntryUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[NotebookEntry, NotebookEntryVersion]:
        """
        Update NotebookEntry content, incrementing current_version and storing a new NotebookEntryVersion.
        """
        new_version_number = db_obj.version + 1
        db_obj.version = new_version_number

        if obj_in.title is not None:
            db_obj.title = obj_in.title
        if obj_in.entry_type is not None:
            db_obj.entry_type = obj_in.entry_type
        if obj_in.content is not None:
            db_obj.content = obj_in.content

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()

        # Create incremental Version snapshot
        version_snapshot = NotebookEntryVersion(
            entry_id=db_obj.id,
            version=new_version_number,
            title=db_obj.title,
            content=db_obj.content,
            created_at=datetime.now(timezone.utc),
        )
        await version_snapshot.insert()
        return db_obj, version_snapshot

    async def list_version_history(
        self, *, notebook_entry_id: UUID
    ) -> List[NotebookEntryVersion]:
        """Fetch all historical versions for a NotebookEntry."""
        return await NotebookEntryVersion.find(
            NotebookEntryVersion.entry_id == notebook_entry_id
        ).sort(-NotebookEntryVersion.version).to_list()

    async def add_attachment(
        self,
        *,
        notebook_entry_id: UUID,
        filename: str,
        blob_path: str,
        mime_type: Optional[str],
        file_size: int,
        checksum: str,
        current_user_id: Optional[UUID] = None
    ) -> NotebookAttachment:
        """Add an attachment to a NotebookEntry."""
        attachment = NotebookAttachment(
            entry_id=notebook_entry_id,
            file_name=filename,
            file_path=blob_path,
        )
        await attachment.insert()
        return attachment

    async def add_comment(
        self,
        *,
        notebook_entry_id: UUID,
        comment: str,
        parent_comment_id: Optional[UUID] = None,
        current_user_id: UUID
    ) -> NotebookComment:
        """Add a comment to a NotebookEntry."""
        c = NotebookComment(
            entry_id=notebook_entry_id,
            comment=comment,
            author_id=current_user_id,
        )
        await c.insert()
        return c

    async def add_tag(
        self,
        *,
        notebook_entry_id: UUID,
        tag_name: str,
        color: str = "#3B82F6"
    ) -> NotebookTag:
        """Add a tag to a NotebookEntry."""
        tag = NotebookTag(
            entry_id=notebook_entry_id,
            tag=tag_name,
        )
        await tag.insert()
        return tag

    async def list_entries(
        self,
        *,
        tenant_id: UUID,
        filter_params: NotebookFilter,
        pagination: NotebookPagination
    ) -> Tuple[List[dict], int]:
        """List and search Notebook entries with filtering and pagination."""
        query = NotebookEntry.find(
            NotebookEntry.tenant_id == tenant_id,
            NotebookEntry.is_deleted == False
        )

        if filter_params.experiment_id:
            query = query.find(NotebookEntry.experiment_id == filter_params.experiment_id)
        if filter_params.entry_type:
            query = query.find(NotebookEntry.entry_type == filter_params.entry_type)
        if filter_params.search:
            query = query.find({"$or": [
                {"title": {"$regex": filter_params.search, "$options": "i"}},
            ]})

        total = await query.count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await query.sort(-NotebookEntry.created_at).skip(skip).limit(pagination.page_size).to_list()
        
        mapped_items = []
        for i in items:
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "experiment_id": i.experiment_id,
                "author_id": i.author_id,
                "title": i.title,
                "content": i.content,
                "entry_type": i.entry_type,
                "version": i.version,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            })
            
        return mapped_items, total

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete Notebook entry."""
        entry = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not entry:
            return False

        entry.is_deleted = True
        entry.updated_at = datetime.now(timezone.utc)
        await entry.save()
        return True


notebook_repo = NotebookRepository()
