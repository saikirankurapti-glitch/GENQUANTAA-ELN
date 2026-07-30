from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.db.enums import RoleStatus

# ==========================================
# Permission Schemas
# ==========================================

class PermissionBase(BaseModel):
    module: str = Field(..., description="The module this permission belongs to (e.g., 'project')")
    resource: str = Field(..., description="The specific resource (e.g., 'study')")
    action: str = Field(..., description="The action allowed (e.g., 'create', 'read')")
    code: str = Field(..., description="Unique permission code (e.g., 'project.create')")
    description: Optional[str] = Field(None, description="Detailed description of what this permission allows")

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    module: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

class PermissionInDBBase(PermissionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PermissionRead(PermissionInDBBase):
    pass

class PermissionListResponse(BaseModel):
    items: List[PermissionRead]
    total: int

# ==========================================
# Role Schemas
# ==========================================

class RoleBase(BaseModel):
    name: str = Field(..., description="Human-readable name of the role")
    code: str = Field(..., description="Unique code for the role within the tenant")
    description: Optional[str] = Field(None, description="Detailed description of the role's purpose")
    is_system: bool = Field(False, description="Whether this is a protected system role")
    status: RoleStatus = Field(RoleStatus.ACTIVE, description="Current status of the role")

class RoleCreate(RoleBase):
    tenant_id: UUID = Field(..., description="The tenant this role belongs to")

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RoleStatus] = None

class RoleInDBBase(RoleBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    
    model_config = ConfigDict(from_attributes=True)

class RoleRead(RoleInDBBase):
    pass

class RoleListResponse(BaseModel):
    items: List[RoleRead]
    total: int

# ==========================================
# Role-Permission Assignment Schemas
# ==========================================

class RolePermissionAssign(BaseModel):
    permission_ids: List[UUID] = Field(..., description="List of permission IDs to assign to the role")

class RolePermissionResponse(BaseModel):
    role_id: UUID
    permission_id: UUID
    granted_at: datetime
    granted_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)

class RoleWithPermissionsRead(RoleRead):
    permissions: List[PermissionRead]
