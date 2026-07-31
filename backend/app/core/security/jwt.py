import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

SECRET_KEY = getattr(settings, "SECRET_KEY", "secret-key-enterprise-eln-jwt-security-key-32bytes")
ALGORITHM = getattr(settings, "ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def create_access_token(
    *,
    user_id: str,
    tenant_id: str,
    organization_id: Optional[str] = None,
    role: str = "Researcher",
    permissions: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token containing all required claims specified in Sprint PDF."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "user_id": str(user_id),
        "tenant_id": str(tenant_id),
        "organization_id": str(organization_id) if organization_id else None,
        "role": role,
        "permissions": permissions or [],
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT Token has expired")
        return None
    except jwt.PyJWTError as e:
        logger.warning(f"Invalid JWT Token: {e}")
        return None
