import logging
from typing import List, Optional, Tuple
from uuid import UUID


from app.crud.crud_experiment import experiment_repo
from app.crud.crud_notebook import notebook_repo
from app.models.identity import User
from app.models.notebook import (
    NotebookAttachment,
    NotebookComment,
    NotebookEntry,
    NotebookEntryVersion,
    NotebookTag,
)
from app.schemas.notebook import (
    NotebookCommentCreate,
    NotebookEntryCreate,
    NotebookEntryUpdate,
    NotebookFilter,
    NotebookPagination,
    NotebookTagCreate,
)

logger = logging.getLogger(__name__)

# Max attachment size: 50MB
MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024


# Domain Exceptions
class NotebookEntryNotFound(Exception):
    pass


class DuplicateNotebookEntryNumber(Exception):
    pass


class ExperimentArchivedOrNotFound(Exception):
    pass


class NotebookEntryLockedError(Exception):
    pass


class InvalidAttachmentError(Exception):
    pass


class NotebookService:
    """Service layer enforcing notebook entry creation, immutable versioning, comments, and attachments."""

    async def create_entry(
        self, *, obj_in: NotebookEntryCreate, tenant_id: UUID, current_user: User
    ) -> NotebookEntry:
        """Create a new notebook entry and initial Version 1 snapshot."""
        # 1. Validate Parent Experiment
        exp = await experiment_repo.get_by_id(db, id=obj_in.experiment_id, tenant_id=tenant_id)
        if not exp:
            raise ExperimentArchivedOrNotFound(f"Parent Experiment {obj_in.experiment_id} not found.")
        if exp.is_archived:
            raise ExperimentArchivedOrNotFound("Cannot create a notebook entry inside an archived Experiment.")

        # 2. Validate Entry Number Uniqueness within Experiment
        existing = await notebook_repo.get_by_number(experiment_id=obj_in.experiment_id, entry_number=obj_in.entry_number, tenant_id=tenant_id
        )
        if existing:
            raise DuplicateNotebookEntryNumber(
                f"Notebook entry number '{obj_in.entry_number}' already exists in Experiment {obj_in.experiment_id}."
            )

        entry = await notebook_repo.create_entry(obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"NotebookService: Created entry '{entry.entry_number}' (ID: {entry.id}) for experiment {obj_in.experiment_id}")
        return entry

    async def get_entry(
        self, *, entry_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> NotebookEntry:
        """Fetch notebook entry by ID or raise NotebookEntryNotFound."""
        entry = await notebook_repo.get_by_id(id=entry_id, tenant_id=tenant_id, include_details=include_details
        )
        if not entry:
            raise NotebookEntryNotFound(f"Notebook entry {entry_id} not found.")
        return entry

    async def update_entry(
        self,
        *, entry_id: UUID,
        obj_in: NotebookEntryUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Tuple[NotebookEntry, NotebookEntryVersion]:
        """Update notebook entry content, creating an immutable new version snapshot."""
        entry = await self.get_entry(entry_id=entry_id, tenant_id=tenant_id)
        if entry.is_locked:
            raise NotebookEntryLockedError("Cannot update a locked notebook entry.")

        updated_entry, new_version = await notebook_repo.update_entry(db_obj=entry, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"NotebookService: Updated entry {entry_id} to version {new_version.version_number}")
        return updated_entry, new_version

    async def list_versions(
        self, *, entry_id: UUID, tenant_id: UUID
    ) -> List[NotebookEntryVersion]:
        """Fetch all historical version snapshots for a notebook entry."""
        await self.get_entry(entry_id=entry_id, tenant_id=tenant_id, include_details=False)
        return await notebook_repo.list_version_history(notebook_entry_id=entry_id)

    async def add_attachment(
        self,
        *, entry_id: UUID,
        filename: str,
        blob_path: str,
        mime_type: Optional[str],
        file_size: int,
        checksum: str,
        tenant_id: UUID,
        current_user: User
    ) -> NotebookAttachment:
        """Add an attachment ensuring size limits."""
        if file_size > MAX_ATTACHMENT_BYTES:
            raise InvalidAttachmentError(f"Attachment file size exceeds maximum limit of 50MB ({file_size} bytes).")

        entry = await self.get_entry(entry_id=entry_id, tenant_id=tenant_id)
        if entry.is_locked:
            raise NotebookEntryLockedError("Cannot add attachments to a locked notebook entry.")

        return await notebook_repo.add_attachment(notebook_entry_id=entry_id,
            filename=filename,
            blob_path=blob_path,
            mime_type=mime_type,
            file_size=file_size,
            checksum=checksum,
            current_user_id=current_user.id,
        )

    async def add_comment(
        self,
        *, entry_id: UUID,
        obj_in: NotebookCommentCreate,
        tenant_id: UUID,
        current_user: User
    ) -> NotebookComment:
        """Add a comment to a notebook entry."""
        await self.get_entry(entry_id=entry_id, tenant_id=tenant_id)
        return await notebook_repo.add_comment(notebook_entry_id=entry_id,
            comment=obj_in.comment,
            parent_comment_id=obj_in.parent_comment_id,
            current_user_id=current_user.id,
        )

    async def add_tag(
        self,
        *, entry_id: UUID,
        obj_in: NotebookTagCreate,
        tenant_id: UUID,
        current_user: User
    ) -> NotebookTag:
        """Add a tag to a notebook entry."""
        await self.get_entry(entry_id=entry_id, tenant_id=tenant_id)
        return await notebook_repo.add_tag(notebook_entry_id=entry_id, tag_name=obj_in.tag_name, color=obj_in.color
        )

    async def list_entries(
        self,
        *, tenant_id: UUID,
        filter_params: NotebookFilter,
        pagination: NotebookPagination
    ) -> Tuple[List[dict], int]:
        """List entries with filtering and pagination."""
        return await notebook_repo.list_entries(tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )


notebook_service = NotebookService()
