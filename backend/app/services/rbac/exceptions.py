class RBACException(Exception):
    """Base exception for RBAC module."""
    pass

class RoleNotFound(RBACException):
    pass

class PermissionNotFound(RBACException):
    pass

class RoleAlreadyExists(RBACException):
    pass

class PermissionAlreadyExists(RBACException):
    pass

class SystemRoleModificationError(RBACException):
    pass

class SystemRoleDeletionError(RBACException):
    pass

class DuplicatePermissionAssignment(RBACException):
    pass

class TenantIsolationError(RBACException):
    pass

class InvalidPermissionCode(RBACException):
    pass

class ValidationError(RBACException):
    pass
