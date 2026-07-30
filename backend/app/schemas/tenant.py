from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.db.enums import TenantStatus

# Shared properties
class TenantBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE

# Properties to receive on creation
class TenantCreate(TenantBase):
    pass

# Properties to receive on update
class TenantUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TenantStatus] = None

# Properties shared by models stored in DB
class TenantInDBBase(TenantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Tenant(TenantInDBBase):
    pass
