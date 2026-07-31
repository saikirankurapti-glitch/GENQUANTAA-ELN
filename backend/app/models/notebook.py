from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4

class NotebookEntry(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    experiment_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    title: str
    content: Optional[str] = None
    entry_type: str = "text"
    version: int = 1
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notebook_entries"

class NotebookEntryVersion(Document):
    id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    version: int
    title: str
    content: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notebook_entry_versions"

class NotebookAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    file_name: str
    file_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notebook_attachments"

class NotebookComment(Document):
    id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    author_id: UUID
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notebook_comments"

class NotebookTag(Document):
    id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    tag: str

    class Settings:
        name = "notebook_tags"
