import base64
import hashlib
import hmac
import logging
import secrets
import struct
import time
from typing import List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_identity import mfa_device_repo
from app.models.identity import MFADevice, User
from app.services.identity.exceptions import (
    InvalidMFACode,
    MFAAlreadyEnabled,
    MFANotEnabled,
)

logger = logging.getLogger(__name__)


class MFAService:
    """Service governing TOTP Multi-Factor Authentication setup and verification."""

    def generate_base32_secret(self) -> str:
        """Generate a cryptographically random 32-character Base32 secret string."""
        raw_bytes = secrets.token_bytes(20)
        return base64.b32encode(raw_bytes).decode("utf-8").replace("=", "")

    def get_totp_uri(self, secret: str, user_email: str, issuer_name: str = "Antigravity ELN") -> str:
        """Construct otpauth:// URI for authenticator app QR code rendering."""
        return f"otpauth://totp/{issuer_name}:{user_email}?secret={secret}&issuer={issuer_name}&algorithm=SHA1&digits=6&period=30"

    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify 6-digit TOTP code against secret with a drift window."""
        try:
            # Clean inputs
            code_str = code.strip()
            if len(code_str) != 6 or not code_str.isdigit():
                return False

            # Add Base32 padding if needed
            padded_secret = secret.upper()
            missing_padding = len(padded_secret) % 8
            if missing_padding:
                padded_secret += "=" * (8 - missing_padding)

            key = base64.b32decode(padded_secret)
            now = int(time.time()) // 30

            for time_step in range(now - window, now + window + 1):
                msg = struct.pack(">Q", time_step)
                hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
                offset = hmac_hash[-1] & 0x0F
                binary = struct.unpack(">I", hmac_hash[offset : offset + 4])[0] & 0x7FFFFFFF
                totp = str(binary % 1_000_000).zfill(6)

                if hmac.compare_digest(totp, code_str):
                    return True
            return False
        except Exception as e:
            logger.error(f"MFAService verification exception: {e}")
            return False

    async def initiate_mfa_setup(
        self, db: AsyncSession, *, user: User, device_name: str = "Primary MFA Device"
    ) -> Tuple[MFADevice, str]:
        """Setup a new MFA device for user and return the object along withotpauth URI."""
        devices = await mfa_device_repo.get_by_user_id(db, user_id=user.id)
        verified_devices = [d for d in devices if d.verified]
        if verified_devices:
            raise MFAAlreadyEnabled("MFA is already enabled and verified for this account.")

        secret = self.generate_base32_secret()
        mfa_device = await mfa_device_repo.create(
            db, user_id=user.id, secret=secret, device_name=device_name, type="totp"
        )
        qr_uri = self.get_totp_uri(secret, user.email)
        logger.info(f"MFAService: Initiated MFA setup for user {user.id}")
        return mfa_device, qr_uri

    async def verify_and_enable_mfa(
        self, db: AsyncSession, *, user_id: UUID, code: str
    ) -> MFADevice:
        """Verify the initial 6-digit TOTP code and enable the MFA device."""
        devices = await mfa_device_repo.get_by_user_id(db, user_id=user_id)
        unverified_devices = [d for d in devices if not d.verified]
        if not unverified_devices:
            raise MFANotEnabled("No unverified MFA device found for setup.")

        target_device = unverified_devices[0]
        if not self.verify_totp_code(target_device.secret, code):
            raise InvalidMFACode("Invalid 6-digit MFA code provided.")

        verified_device = await mfa_device_repo.verify_device(db, id=target_device.id)
        await mfa_device_repo.update_last_used(db, id=target_device.id)
        logger.info(f"MFAService: Successfully verified and enabled MFA for user {user_id}")
        return verified_device

    async def validate_user_mfa(self, db: AsyncSession, *, user_id: UUID, code: str) -> bool:
        """Validate 6-digit TOTP code during login or step-up authentication."""
        devices = await mfa_device_repo.get_by_user_id(db, user_id=user_id)
        verified_devices = [d for d in devices if d.verified]
        if not verified_devices:
            return True  # If MFA is not enabled, validation passes

        device = verified_devices[0]
        if not self.verify_totp_code(device.secret, code):
            raise InvalidMFACode("Invalid 6-digit MFA verification code.")

        await mfa_device_repo.update_last_used(db, id=device.id)
        return True

    async def disable_mfa(self, db: AsyncSession, *, user_id: UUID) -> bool:
        """Disable and remove all MFA devices for user."""
        devices = await mfa_device_repo.get_by_user_id(db, user_id=user_id)
        for device in devices:
            await mfa_device_repo.hard_delete(db, id=device.id)
        logger.info(f"MFAService: Disabled MFA for user {user_id}")
        return True


mfa_service = MFAService()
