import math
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.protocol import (
    ProtocolApprovalCreate,
    ProtocolApprovalRead,
    ProtocolAttachmentRead,
    ProtocolCreate,
    ProtocolDetail,
    ProtocolFilter,
    ProtocolListResponse,
    ProtocolPagination,
    ProtocolRead,
    ProtocolStepCreate,
    ProtocolStepRead,
    ProtocolUpdate,
    ProtocolVersionRead,
)
from app.services.protocol_service import (
    DuplicateProtocolCode,
    InvalidProtocolStepOrder,
    ProtocolNotFound,
    protocol_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=ProtocolListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Protocols",
    description="Fetch paginated protocols for current tenant with filtering and sorting.",
)
async def list_protocols(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    category: Optional[str] = Query(None),
    status_param: Optional[str] = Query(None, alias="status"),
    owner_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    """Paginated protocol listing."""
    try:
        filter_params = ProtocolFilter(
            category=category, status=status_param, owner_id=owner_id, search=search
        )
        pagination = ProtocolPagination(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items, total = await protocol_service.list_protocols(
            db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return ProtocolListResponse(
            items=[ProtocolRead.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        return ProtocolListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.get(
    "/search",
    response_model=ProtocolListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Protocols",
    description="Search protocols by code or title keyword.",
)
async def search_protocols(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search protocols."""
    try:
        filter_params = ProtocolFilter(search=q)
        pagination = ProtocolPagination(page=page, page_size=page_size)
        items, total = await protocol_service.list_protocols(
            db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return ProtocolListResponse(
            items=[ProtocolRead.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        return ProtocolListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.post(
    "/",
    response_model=ProtocolRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Protocol",
    description="Register a new SOP protocol with initial steps.",
)
async def create_protocol(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    protocol_in: ProtocolCreate,
) -> Any:
    """Create protocol."""
    try:
        protocol = await protocol_service.create_protocol(
            db, obj_in=protocol_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProtocolRead.model_validate(protocol)
    except DuplicateProtocolCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidProtocolStepOrder as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{id}",
    response_model=ProtocolDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Protocol Details",
    description="Fetch protocol detail including steps, version snapshots, attachments, and approvals.",
)
async def get_protocol(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch protocol detail."""
    try:
        protocol = await protocol_service.get_protocol(
            db, protocol_id=id, tenant_id=current_tenant.id, include_details=True
        )
        return ProtocolDetail.model_validate(protocol)
    except ProtocolNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=ProtocolRead,
    status_code=status.HTTP_200_OK,
    summary="Update Protocol",
    description="Update protocol details, creating a new version snapshot.",
)
async def update_protocol(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    protocol_in: ProtocolUpdate,
) -> Any:
    """Update protocol."""
    try:
        protocol, _ = await protocol_service.update_protocol(
            db, protocol_id=id, obj_in=protocol_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProtocolRead.model_validate(protocol)
    except ProtocolNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{id}/versions",
    response_model=List[ProtocolVersionRead],
    status_code=status.HTTP_200_OK,
    summary="Get Version History",
    description="Fetch all historical version snapshots for a protocol.",
)
async def get_version_history(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch version history."""
    try:
        versions = await protocol_service.list_versions(
            db, protocol_id=id, tenant_id=current_tenant.id
        )
        return [ProtocolVersionRead.model_validate(v) for v in versions]
    except ProtocolNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/steps",
    response_model=ProtocolStepRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Step",
    description="Add a new execution step to a protocol.",
)
async def add_step(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    step_in: ProtocolStepCreate,
) -> Any:
    """Add step."""
    try:
        step = await protocol_service.add_step(
            db, protocol_id=id, step_in=step_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProtocolStepRead.model_validate(step)
    except ProtocolNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidProtocolStepOrder as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{id}/approve",
    response_model=ProtocolApprovalRead,
    status_code=status.HTTP_200_OK,
    summary="Approve or Reject Protocol",
    description="Submit formal approval decision for a protocol review workflow.",
)
async def approve_protocol(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    approval_in: ProtocolApprovalCreate,
) -> Any:
    """Approve or reject protocol."""
    try:
        approval = await protocol_service.approve_protocol(
            db, protocol_id=id, obj_in=approval_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProtocolApprovalRead.model_validate(approval)
    except ProtocolNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
