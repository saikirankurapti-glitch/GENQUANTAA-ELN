import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user, get_current_tenant
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Aggregated ELN Dashboard Data",
    description="""
    Fetch aggregated metrics, active projects, recent experiments, pending notifications,
    quick create actions, AI Copilot shortcuts, and recent activity feed for the current user and tenant.
    """,
)
async def get_dashboard(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Return single aggregated DashboardResponse object."""
    return await dashboard_service.get_dashboard(
        db, user=current_user, tenant_id=current_tenant.id
    )
