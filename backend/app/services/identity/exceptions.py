class IdentityException(Exception):
    """Base exception for Identity module."""
    pass


class UserNotFound(IdentityException):
    """Raised when user account is not found in the tenant scope."""
    pass


class UserAlreadyExists(IdentityException):
    """Raised when username, email, or employee_id already exists within tenant."""
    pass


class InvalidCredentials(IdentityException):
    """Raised on invalid username/password combinations."""
    pass


class AccountLocked(IdentityException):
    """Raised when account is locked due to brute force protection."""
    pass


class AccountDisabled(IdentityException):
    """Raised when account status is inactive or suspended."""
    pass


class MustChangePassword(IdentityException):
    """Raised when user must force reset password before continuing."""
    pass


class PasswordPolicyError(IdentityException):
    """Raised when new password fails complexity rules."""
    pass


class PasswordReuseError(IdentityException):
    """Raised when user attempts to re-use a recent password."""
    pass


class InvalidToken(IdentityException):
    """Raised when JWT, refresh token, or verification token is invalid."""
    pass


class TokenExpired(IdentityException):
    """Raised when authentication token has expired."""
    pass


class MFARequired(IdentityException):
    """Raised when 2FA code is missing during login."""
    pass


class InvalidMFACode(IdentityException):
    """Raised when 6-digit TOTP code is incorrect."""
    pass


class MFAAlreadyEnabled(IdentityException):
    """Raised when MFA setup is attempted on an already verified device."""
    pass


class MFANotEnabled(IdentityException):
    """Raised when MFA operations are called for a user without MFA."""
    pass


class ApiKeyNotFound(IdentityException):
    """Raised when API Key is not found."""
    pass


class ApiKeyExpired(IdentityException):
    """Raised when API Key has expired."""
    pass


class InvalidApiKey(IdentityException):
    """Raised when API Key hash fails verification."""
    pass


class SessionNotFound(IdentityException):
    """Raised when session token is invalid or terminated."""
    pass


class SessionExpired(IdentityException):
    """Raised when user session window has elapsed."""
    pass


class TenantIsolationError(IdentityException):
    """Raised when tenant boundaries are violated."""
    pass


class UnauthorizedAction(IdentityException):
    """Raised when permission/role checks fail."""
    pass
