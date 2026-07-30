import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        db: AsyncSession,
        *,
        obj_in: NotebookEntryCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> NotebookEntry:
        """Create a new NotebookEntry and its initial NotebookEntryVersion (version 1)."""
        entry = NotebookEntry(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            experiment_id=obj_in.experiment_id,
            entry_number=obj_in.entry_number,
            title=obj_in.title,
            content=obj_in.content,
            entry_type=obj_in.entry_type,
            current_version=1,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(entry)
        await db.flush()  # Obtain entry.id before adding version

        # Create initial Version 1 snapshot
        initial_version = NotebookEntryVersion(
            notebook_entry_id=entry.id,
            version_number=1,
            content_snapshot=obj_in.content,
            change_reason="Initial creation of notebook entry.",
            created_by=current_user_id,
        )
        db.add(initial_version)
        await db.commit()
        await db.refresh(entry)
        return entry

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[NotebookEntry]:
        """Fetch NotebookEntry by ID within tenant scope."""
        stmt = select(NotebookEntry).where(
            NotebookEntry.id == id,
            NotebookEntry.tenant_id == tenant_id,
            NotebookEntry.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(NotebookEntry.versions),
                selectinload(NotebookEntry.attachments),
                selectinload(NotebookEntry.comments),
                selectinload(NotebookEntry.tags),
                selectinload(NotebookEntry.experiment),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(
        self, db: AsyncSession, *, experiment_id: UUID, entry_number: str, tenant_id: UUID
    ) -> Optional[NotebookEntry]:
        """Fetch NotebookEntry by entry_number within experiment and tenant scope."""
        stmt = select(NotebookEntry).where(
            NotebookEntry.experiment_id == experiment_id,
            NotebookEntry.entry_number == entry_number.upper(),
            NotebookEntry.tenant_id == tenant_id,
            NotebookEntry.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_entry(
        self,
        db: AsyncSession,
        *,
        db_obj: NotebookEntry,
        obj_in: NotebookEntryUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[NotebookEntry, NotebookEntryVersion]:
        """
        Update NotebookEntry content, incrementing current_version and storing a new NotebookEntryVersion.
        """
        new_version_number = db_obj.current_version + 1
        db_obj.current_version = new_version_number

        if obj_in.title is not None:
            db_obj.title = obj_in.title
        if obj_in.entry_type is not None:
            db_obj.entry_type = obj_in.entry_type
        if obj_in.content is not None:
            db_obj.content = obj_in.content

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)

        # Create incremental Version snapshot
        version_snapshot = NotebookEntryVersion(
            notebook_entry_id=db_obj.id,
            version_number=new_version_number,
            content_snapshot=db_obj.content,
            change_reason=obj_in.change_reason or f"Updated to version {new_version_number}",
            created_by=current_user_id,
        )
        db.add(version_snapshot)
        await db.commit()
        await db.refresh(db_obj)
        await db.refresh(version_snapshot)
        return db_obj, version_snapshot

    async def list_version_history(
        self, db: AsyncSession, *, notebook_entry_id: UUID
    ) -> List[NotebookEntryVersion]:
        """Fetch all historical versions for a NotebookEntry."""
        stmt = (
            select(NotebookEntryVersion)
            .where(NotebookEntryVersion.notebook_entry_id == notebook_entry_id)
            .order_by(NotebookEntryVersion.version_number.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_attachment(
        self,
        db: AsyncSession,
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
            notebook_entry_id=notebook_entry_id,
            filename=filename,
            blob_path=blob_path,
            mime_type=mime_type,
            file_size=file_size,
            checksum=checksum,
            uploaded_by=current_user_id,
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        return attachment

    async def add_comment(
        self,
        db: AsyncSession,
        *,
        notebook_entry_id: UUID,
        comment: str,
        parent_comment_id: Optional[UUID] = None,
        current_user_id: UUID
    ) -> NotebookComment:
        """Add a comment to a NotebookEntry."""
        c = NotebookComment(
            notebook_entry_id=notebook_entry_id,
            comment=comment,
            parent_comment_id=parent_comment_id,
            author_id=current_user_id,
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c

    async def add_tag(
        self,
        db: AsyncSession,
        *,
        notebook_entry_id: UUID,
        tag_name: str,
        color: str = "#3B82F6"
    ) -> NotebookTag:
        """Add a tag to a NotebookEntry."""
        tag = NotebookTag(
            notebook_entry_id=notebook_entry_id,
            tag_name=tag_name,
            color=color,
        )
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    async def list_entries(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: NotebookFilter,
        pagination: NotebookPagination
    ) -> Tuple[List[NotebookEntry], int]:
        """List and search Notebook entries with filtering and pagination."""
        query = select(NotebookEntry).where(
            NotebookEntry.tenant_id == tenant_id,
            NotebookEntry.is_deleted == False
        )

        if filter_params.experiment_id:
            query = query.where(NotebookEntry.experiment_id == filter_params.experiment_id)
        if filter_params.entry_type:
            query = query.where(NotebookEntry.entry_type == filter_params.entry_type)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    NotebookEntry.entry_number.ilike(pattern),
                    NotebookEntry.title.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(NotebookEntry, pagination.sort_by, NotebookEntry.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete Notebook entry."""
        entry = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not entry:
            return False

        entry.is_deleted = True
        entry.deleted_at = datetime.now(timezone.utc)
        entry.deleted_by = current_user_id
        db.add(entry)
        await db.commit()
        return True


notebook_repo = NotebookRepository()
