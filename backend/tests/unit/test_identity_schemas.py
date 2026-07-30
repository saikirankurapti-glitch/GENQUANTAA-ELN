import uuid
import pytest
from pydantic import ValidationError

from app.schemas.identity import (
    ApiKeyCreateResponse,
    ApiKeyRead,
    MFADeviceVerifyRequest,
    UserCreate,
    UserLoginRequest,
    UserRead,
)


@pytest.mark.unit
def test_user_create_valid_schema():
    """Test valid UserCreate schema validation."""
    tenant_id = uuid.uuid4()
    data = {
        "username": "valid_user",
        "email": "user@organization.com",
        "first_name": "Alice",
        "last_name": "Smith",
        "password": "StrongPassword123!",
        "tenant_id": str(tenant_id),
        "phone_number": "+14155552671",
    }
    user_create = UserCreate(**data)
    assert user_create.username == "valid_user"
    assert user_create.email == "user@organization.com"
    assert user_create.phone_number == "+14155552671"


@pytest.mark.unit
def test_user_create_invalid_password_complexity():
    """Test password complexity rejection."""
    tenant_id = uuid.uuid4()
    base_data = {
        "username": "valid_user",
        "email": "user@organization.com",
        "first_name": "Alice",
        "last_name": "Smith",
        "tenant_id": str(tenant_id),
    }

    # Too short (<12 chars)
    with pytest.raises(ValidationError):
        UserCreate(**base_data, password="Short1!")

    # Missing uppercase
    with pytest.raises(ValidationError):
        UserCreate(**base_data, password="lowercase123!")

    # Missing special character
    with pytest.raises(ValidationError):
        UserCreate(**base_data, password="NoSpecialChar123")


@pytest.mark.unit
def test_user_create_invalid_username():
    """Test username regex rejection."""
    tenant_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        UserCreate(
            username="invalid user@space",
            email="user@org.com",
            first_name="Alice",
            last_name="Smith",
            password="StrongPassword123!",
            tenant_id=str(tenant_id),
        )


@pytest.mark.unit
def test_totp_mfa_code_validation():
    """Test 6-digit TOTP code validation."""
    valid_req = MFADeviceVerifyRequest(code="123456")
    assert valid_req.code == "123456"

    # Non-digit or wrong length
    with pytest.raises(ValidationError):
        MFADeviceVerifyRequest(code="12345")

    with pytest.raises(ValidationError):
        MFADeviceVerifyRequest(code="ABCDEF")


@pytest.mark.unit
def test_sensitive_field_stripping():
    """Ensure password hashes, secrets, and raw keys are excluded from Read models."""
    api_key_read_fields = ApiKeyRead.model_fields.keys()
    assert "hashed_key" not in api_key_read_fields

    user_read_fields = UserRead.model_fields.keys()
    assert "password_hash" not in user_read_fields
