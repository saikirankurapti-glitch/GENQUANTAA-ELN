import re
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from app.db.enums import UserStatus


# ==========================================
# Regular Expression Patterns & Validators
# ==========================================
USERNAME_REGEX = r"^[a-zA-Z0-9_-]+$"
PHONE_E164_REGEX = r"^\+?[1-9]\d{1,14}$"
TOTP_CODE_REGEX = r"^\d{6}$"


# ==========================================
# User Profile Schemas
# ==========================================

class UserProfileBase(BaseModel):
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=32, description="Gender preference")
    department: Optional[str] = Field(None, max_length=128, description="Department name")
    designation: Optional[str] = Field(None, max_length=128, description="Job designation or title")
    location: Optional[str] = Field(None, max_length=255, description="Physical location or facility")
    time_zone: Optional[str] = Field("UTC", max_length=64, description="Preferred IANA timezone")
    language: Optional[str] = Field("en", max_length=16, description="Preferred language ISO code")
    avatar_url: Optional[str] = Field(None, max_length=512, description="Avatar image storage URL")
    biography: Optional[str] = Field(None, description="User biography or summary")


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=32)
    department: Optional[str] = Field(None, max_length=128)
    designation: Optional[str] = Field(None, max_length=128)
    location: Optional[str] = Field(None, max_length=255)
    time_zone: Optional[str] = Field(None, max_length=64)
    language: Optional[str] = Field(None, max_length=16)
    avatar_url: Optional[str] = Field(None, max_length=512)
    biography: Optional[str] = None


class UserProfileRead(UserProfileBase):
    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# User Role Assignment Schemas
# ==========================================

class UserRoleBase(BaseModel):
    role_id: UUID = Field(..., description="Target Role ID to assign")
    expires_at: Optional[datetime] = Field(None, description="Optional temporary assignment expiration")
    is_primary: bool = Field(False, description="Whether this is the user's primary role")
    is_active: bool = Field(True, description="Whether this assignment is active")


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None


class UserRoleRead(UserRoleBase):
    id: UUID
    user_id: UUID
    assigned_by: Optional[UUID] = None
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# User Preference Schemas
# ==========================================

class UserPreferenceBase(BaseModel):
    theme: str = Field("light", max_length=32, description="UI layout theme (e.g. 'light', 'dark')")
    language: str = Field("en", max_length=16, description="Interface language code")
    time_zone: str = Field("UTC", max_length=64, description="User local time zone")
    notification_settings: dict = Field(default_factory=dict, description="Notification channels preferences JSON")


class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = Field(None, max_length=32)
    language: Optional[str] = Field(None, max_length=16)
    time_zone: Optional[str] = Field(None, max_length=64)
    notification_settings: Optional[dict] = None


class UserPreferenceRead(UserPreferenceBase):
    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Electronic Signature Profile Schemas
# ==========================================

class ElectronicSignatureProfileBase(BaseModel):
    signature_meaning: Optional[str] = Field(None, max_length=255, description="Default signing intention text")
    signature_algorithm: Optional[str] = Field(None, max_length=64, description="Signature algorithm name")
    certificate_thumbprint: Optional[str] = Field(None, max_length=255, description="Digital cert thumbprint")
    enabled: bool = Field(True, description="Whether electronic signing is active for this user")


class ElectronicSignatureProfileCreate(ElectronicSignatureProfileBase):
    pass


class ElectronicSignatureProfileUpdate(BaseModel):
    signature_meaning: Optional[str] = Field(None, max_length=255)
    signature_algorithm: Optional[str] = Field(None, max_length=64)
    certificate_thumbprint: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None


class ElectronicSignatureProfileRead(ElectronicSignatureProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Core User Schemas
# ==========================================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=128, description="Unique login username")
    email: EmailStr = Field(..., max_length=255, description="Corporate email address")
    employee_id: Optional[str] = Field(None, max_length=64, description="Corporate HR employee identifier")
    first_name: str = Field(..., min_length=1, max_length=128, description="Legal first name")
    last_name: str = Field(..., min_length=1, max_length=128, description="Legal last name")
    display_name: Optional[str] = Field(None, max_length=255, description="Preferred display name")
    phone_number: Optional[str] = Field(None, max_length=32, description="E.164 phone number")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(USERNAME_REGEX, v):
            raise ValueError("Username must contain only alphanumeric characters, underscores, or hyphens.")
        return v.lower().strip()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if not re.match(PHONE_E164_REGEX, v):
                raise ValueError("Phone number must follow standard E.164 format (e.g. +1234567890).")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, description="Plaintext password meeting complexity requirements")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: Optional[UUID] = Field(None, description="Optional organization identifier")
    profile: Optional[UserProfileCreate] = Field(None, description="Optional initial user profile data")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one numeric digit.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class UserUpdate(BaseModel):
    employee_id: Optional[str] = Field(None, max_length=64)
    first_name: Optional[str] = Field(None, min_length=1, max_length=128)
    last_name: Optional[str] = Field(None, min_length=1, max_length=128)
    display_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=32)
    organization_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if not re.match(PHONE_E164_REGEX, v):
                raise ValueError("Phone number must follow standard E.164 format.")
        return v


class UserChangePassword(BaseModel):
    current_password: str = Field(..., description="User's current password")
    new_password: str = Field(..., min_length=12, description="New password complying with complexity policy")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return UserCreate.validate_password_complexity(v)


class UserForgotPassword(BaseModel):
    email: EmailStr = Field(..., description="Email associated with account")


class UserResetPassword(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=12, description="New password complying with complexity policy")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return UserCreate.validate_password_complexity(v)


class UserInDBBase(UserBase):
    id: UUID
    tenant_id: UUID
    organization_id: Optional[UUID] = None
    must_change_password: bool
    email_verified: bool
    phone_verified: bool
    is_active: bool
    is_locked: bool
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserInDBBase):
    profile: Optional[UserProfileRead] = None
    roles: List[UserRoleRead] = Field(default_factory=list)


class UserDetailRead(UserRead):
    preference: Optional[UserPreferenceRead] = None
    signature_profile: Optional[ElectronicSignatureProfileRead] = None


class UserFilter(BaseModel):
    tenant_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search query string matching name, email, or username")


class UserPagination(BaseModel):
    items: List[UserRead]
    total: int = Field(..., description="Total matching user records count")
    page: int = Field(1, description="Current page number")
    size: int = Field(50, description="Items per page limit")
    pages: int = Field(..., description="Total calculated pages")


# ==========================================
# Authentication & Session Request Schemas
# ==========================================

class UserLoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")
    mfa_code: Optional[str] = Field(None, description="Optional 6-digit TOTP code if MFA enabled")
    device_identifier: Optional[str] = Field(None, max_length=255, description="Client device fingerprint")
    device_name: Optional[str] = Field(None, max_length=255, description="Human readable device name")

    @field_validator("mfa_code")
    @classmethod
    def validate_mfa_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if not re.match(TOTP_CODE_REGEX, v):
                raise ValueError("MFA code must be a 6-digit number.")
        return v


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field("bearer", description="Token type header")
    expires_in: int = Field(..., description="Access token expiration window in seconds")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT Refresh Token")


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token string")


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to resend verification link")


# ==========================================
# Session Schemas
# ==========================================

class UserSessionRead(BaseModel):
    id: UUID
    user_id: UUID
    device_name: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    last_activity: datetime
    expires_at: datetime
    is_revoked: bool

    model_config = ConfigDict(from_attributes=True)


class UserSessionListResponse(BaseModel):
    items: List[UserSessionRead]
    total: int


# ==========================================
# Login History Schemas
# ==========================================

class LoginHistoryRead(BaseModel):
    id: UUID
    user_id: UUID
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: Optional[str] = None
    device: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoginHistoryListResponse(BaseModel):
    items: List[LoginHistoryRead]
    total: int


# ==========================================
# Password History Schemas
# ==========================================

class PasswordHistoryRead(BaseModel):
    id: UUID
    user_id: UUID
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MFA Device Schemas
# ==========================================

class MFADeviceSetupRequest(BaseModel):
    device_name: str = Field("Primary MFA Device", max_length=255, description="Device label")


class MFADeviceSetupResponse(BaseModel):
    id: UUID
    secret: str = Field(..., description="Base32 TOTP secret string (Show ONCE during setup)")
    qr_code_url: str = Field(..., description="otpauth:// URL for QR code generation")


class MFADeviceVerifyRequest(BaseModel):
    code: str = Field(..., description="6-digit TOTP validation code")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.match(TOTP_CODE_REGEX, v):
            raise ValueError("TOTP code must be a 6-digit number.")
        return v


class MFADeviceRead(BaseModel):
    id: UUID
    user_id: UUID
    device_name: str
    type: str
    verified: bool
    verified_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MFADeviceListResponse(BaseModel):
    items: List[MFADeviceRead]
    total: int


# ==========================================
# API Key Schemas
# ==========================================

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Description of the key usage")
    expires_at: Optional[datetime] = Field(None, description="Optional key expiration date")


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    api_key: str = Field(..., description="Raw secret API key (Displayed ONLY ONCE on creation)")
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyRead(BaseModel):
    id: UUID
    user_id: UUID
    tenant_id: UUID
    name: str
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyRead]
    total: int


# ==========================================
# Trusted Device Schemas
# ==========================================

class TrustedDeviceRead(BaseModel):
    id: UUID
    user_id: UUID
    device_identifier: str
    device_name: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    ip_address: Optional[str] = None
    trusted_since: datetime
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


class TrustedDeviceListResponse(BaseModel):
    items: List[TrustedDeviceRead]
    total: int
