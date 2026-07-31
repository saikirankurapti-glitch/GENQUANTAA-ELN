from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4

class Protocol(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    author_id: Optional[UUID] = None
    title: str
    protocol_code: str
    category: str = "general"
    status: str = "active"
    description: Optional[str] = None
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "protocols"

class ProtocolVersion(Document):
    id: UUID = Field(default_factory=uuid4)
    protocol_id: UUID
    version: int
    title: str
    content: Optional[str] = None

    class Settings:
        name = "protocol_versions"

class ProtocolStep(Document):
    id: UUID = Field(default_factory=uuid4)
    protocol_id: UUID
    step_order: int
    title: str
    instructions: Optional[str] = None

    class Settings:
        name = "protocol_steps"

class ProtocolAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    protocol_id: UUID
    file_name: str
    file_path: str

    class Settings:
        name = "protocol_attachments"

class ProtocolApproval(Document):
    id: UUID = Field(default_factory=uuid4)
    protocol_id: UUID
    approver_id: UUID
    status: str = "pending"

    class Settings:
        name = "protocol_approvals"
