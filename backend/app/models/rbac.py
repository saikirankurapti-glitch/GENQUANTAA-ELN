from typing import Optional, List
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4
from app.db.enums import RoleStatus

class Role(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: Optional[UUID] = None
    name: str
    code: str
    description: Optional[str] = None
    is_system_role: bool = False
    status: RoleStatus = RoleStatus.ACTIVE
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "roles"

class Permission(Document):
    id: UUID = Field(default_factory=uuid4)
    name: str
    code: str
    module: str = "general"
    description: Optional[str] = None

    class Settings:
        name = "permissions"

class RolePermission(Document):
    id: UUID = Field(default_factory=uuid4)
    role_id: UUID
    permission_id: UUID

    class Settings:
        name = "role_permissions"
