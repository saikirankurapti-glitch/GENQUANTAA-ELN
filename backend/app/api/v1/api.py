from fastapi import APIRouter
from app.api.v1.endpoints import (
    tenants, roles, permissions, role_permissions, dashboard,
    projects, experiments, notebook, samples, protocols,
    inventory, instruments, sequences, ai_copilot, notifications,
)
from app.api.v1.endpoints.router import identity_router

api_router = APIRouter()

api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(role_permissions.router, tags=["Role Permissions"])
api_router.include_router(identity_router)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard Module"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications Module"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects Module"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments Module"])
api_router.include_router(notebook.router, prefix="/notebook", tags=["ELN Notebook Module"])
api_router.include_router(samples.router, prefix="/samples", tags=["Sample Registry Module"])
api_router.include_router(protocols.router, prefix="/protocols", tags=["Protocol Management Module"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory Management Module"])
api_router.include_router(instruments.router, prefix="/instruments", tags=["Instrument Management Module"])
api_router.include_router(sequences.router, prefix="/sequences", tags=["Sequence Management Module"])
api_router.include_router(ai_copilot.router, prefix="/ai", tags=["AI Copilot Module"])
