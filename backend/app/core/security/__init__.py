# Expose dependencies for easy import
from .authorization import (
    get_current_user,
    get_current_active_user,
    get_current_tenant,
    require_role,
    require_any_role,
    require_all_roles,
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_system_admin,
    require_organization_admin
)
