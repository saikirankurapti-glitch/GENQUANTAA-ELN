from fastapi import APIRouter

from app.api.v1.endpoints import (
    api_keys,
    auth,
    electronic_signatures,
    mfa,
    preferences,
    profiles,
    sessions,
    trusted_devices,
    user_roles,
    users,
)

identity_router = APIRouter()

identity_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Security"])
identity_router.include_router(users.router, prefix="/users", tags=["User Management"])
identity_router.include_router(profiles.router, prefix="/profiles", tags=["User Profiles"])
identity_router.include_router(user_roles.router, tags=["User Role Assignments"])
identity_router.include_router(sessions.router, prefix="/sessions", tags=["Session Management"])
identity_router.include_router(mfa.router, prefix="/mfa", tags=["MFA Security"])
identity_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Key Management"])
identity_router.include_router(trusted_devices.router, prefix="/trusted-devices", tags=["Trusted Devices"])
identity_router.include_router(preferences.router, prefix="/preferences", tags=["User Preferences"])
identity_router.include_router(electronic_signatures.router, prefix="/electronic-signatures", tags=["Electronic Signatures (FDA Part 11)"])
