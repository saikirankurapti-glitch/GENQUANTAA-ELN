import uuid
from datetime import datetime, timezone
import pytest

from app.db.base import Base, Tenant, Organization, Role  # Register all mappers
from app.models.identity import (
    ApiKey,
    ElectronicSignatureProfile,
    LoginHistory,
    MFADevice,
    PasswordHistory,
    RefreshToken,
    TrustedDevice,
    User,
    UserProfile,
    UserPreference,
    UserRole,
    UserSession,
)
from app.db.enums import UserStatus


@pytest.mark.unit
def test_user_model_instantiation():
    """Test User model default fields and attributes."""
    tenant_id = uuid.uuid4()
    user = User(
        tenant_id=tenant_id,
        username="test_scientist",
        email="scientist@lab.com",
        first_name="Jane",
        last_name="Doe",
        password_hash="pbkdf2_sha256$100000$salt$hash",
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        must_change_password=False,
        status=UserStatus.ACTIVE,
    )
    assert user.username == "test_scientist"
    assert user.email == "scientist@lab.com"
    assert user.is_active is True
    assert user.is_locked is False
    assert user.failed_login_attempts == 0
    assert user.must_change_password is False
    assert user.status == UserStatus.ACTIVE


@pytest.mark.unit
def test_user_profile_model():
    """Test UserProfile model instantiation."""
    user_id = uuid.uuid4()
    profile = UserProfile(
        user_id=user_id,
        department="Biochemistry",
        designation="Senior Researcher",
        time_zone="UTC",
        language="en",
    )
    assert profile.user_id == user_id
    assert profile.department == "Biochemistry"
    assert profile.time_zone == "UTC"


@pytest.mark.unit
def test_mfa_device_model():
    """Test MFADevice default values."""
    user_id = uuid.uuid4()
    mfa = MFADevice(
        user_id=user_id,
        secret="JBSWY3DPEHPK3PXP",
        device_name="Primary Phone",
        type="totp",
        verified=False,
    )
    assert mfa.user_id == user_id
    assert mfa.secret == "JBSWY3DPEHPK3PXP"
    assert mfa.verified is False


@pytest.mark.unit
def test_api_key_model():
    """Test ApiKey model attributes."""
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    api_key = ApiKey(
        tenant_id=tenant_id,
        user_id=user_id,
        name="Integration Pipeline",
        hashed_key="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_active=True,
    )
    assert api_key.name == "Integration Pipeline"
    assert api_key.is_active is True
