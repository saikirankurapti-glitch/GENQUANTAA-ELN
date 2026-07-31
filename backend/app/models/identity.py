from typing import Optional, List
from datetime import datetime, timezone
from pydantic import Field, EmailStr
from beanie import Document
from uuid import UUID, uuid4
from app.db.enums import UserStatus

class User(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    password_hash: str
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    must_change_password: bool = False
    email_verified: bool = False
    phone_verified: bool = False
    status: UserStatus = UserStatus.ACTIVE
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

class UserProfile(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    time_zone: str = "UTC"
    language: str = "en"
    avatar_url: Optional[str] = None
    biography: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "user_profiles"

class UserRole(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    role_id: UUID = Field(default_factory=uuid4)
    role_name: str = "Researcher"
    is_primary: bool = True
    is_active: bool = True
    assigned_by: Optional[UUID] = None
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    class Settings:
        name = "user_roles"

class UserPreference(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    theme: str = "light"
    language: str = "en"
    notifications_enabled: bool = True

    class Settings:
        name = "user_preferences"

class RefreshToken(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    token: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "refresh_tokens"

class UserSession(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "user_sessions"

class ApiKey(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    user_id: UUID
    name: str
    hashed_key: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "api_keys"

class MFADevice(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    secret: str
    device_name: str = "Primary Device"
    type: str = "totp"
    verified: bool = False

    class Settings:
        name = "mfa_devices"

class TrustedDevice(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    device_fingerprint: str
    device_name: str
    is_active: bool = True

    class Settings:
        name = "trusted_devices"

class ElectronicSignatureProfile(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    signature_title: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "electronic_signature_profiles"

class LoginHistory(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "login_history"

class PasswordHistory(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "password_history"
