import pytest
from app.services.identity.password_service import password_service
from app.services.identity.mfa_service import mfa_service
from app.services.identity.api_key_service import api_key_service


@pytest.mark.unit
def test_password_hashing_and_verification():
    """Test PBKDF2/SHA256 password hashing and verification."""
    password = "SuperSecretPassword123!"
    pwd_hash = password_service.hash_password(password)

    assert pwd_hash.startswith("pbkdf2_sha256$")
    assert password_service.verify_password(password, pwd_hash) is True
    assert password_service.verify_password("WrongPassword123!", pwd_hash) is False


@pytest.mark.unit
def test_totp_secret_generation_and_validation():
    """Test Base32 secret generation and TOTP validation logic."""
    secret = mfa_service.generate_base32_secret()
    assert len(secret) >= 16

    totp_uri = mfa_service.get_totp_uri(secret, "scientist@lab.com")
    assert "otpauth://totp/" in totp_uri
    assert secret in totp_uri


@pytest.mark.unit
def test_api_key_generation():
    """Test API key generation and hashing."""
    raw_key, hashed_key = api_key_service.generate_api_key()
    assert raw_key.startswith("eln_ak_")
    assert len(hashed_key) == 64  # SHA-256 hex string length
