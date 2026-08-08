import math
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
)
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.sample import (
    ChainOfCustodyRead,
    SampleAttachmentRead,
    SampleCreate,
    SampleDetail,
    SampleFilter,
    SampleListResponse,
    SamplePagination,
    SampleRead,
    SampleUpdate,
)
from app.services.sample_service import (
    DuplicateSampleBarcode,
    DuplicateSampleCode,
    ExperimentArchivedOrNotFound,
    InvalidSampleQuantityError,
    SampleArchivedError,
    SampleNotFound,
    sample_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=SampleListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Samples",
    description="Fetch paginated sample records for current tenant with filtering and sorting.",
)
async def list_samples(    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    experiment_id: Optional[UUID] = Query(None),
    sample_type_id: Optional[UUID] = Query(None),
    storage_location_id: Optional[UUID] = Query(None),
    status_param: Optional[str] = Query(None, alias="status"),
    barcode: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    """Paginated sample listing."""
    try:
        filter_params = SampleFilter(
            experiment_id=experiment_id,
            sample_type_id=sample_type_id,
            storage_location_id=storage_location_id,
            status=status_param,
            barcode=barcode,
            search=search,
        )
        pagination = SamplePagination(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items, total = await sample_service.list_samples(tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return SampleListResponse(
            items=[SampleRead.model_validate(s) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        return SampleListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.get(
    "/search",
    response_model=SampleListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Samples",
    description="Search samples by code, barcode, or name query.",
)
async def search_samples(    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search samples."""
    try:
        filter_params = SampleFilter(search=q)
        pagination = SamplePagination(page=page, page_size=page_size)
        items, total = await sample_service.list_samples(tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return SampleListResponse(
            items=[SampleRead.model_validate(s) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        return SampleListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.post(
    "/",
    response_model=SampleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Sample",
    description="Register a new biological or chemical sample.",
)
async def create_sample(
    *,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    sample_in: SampleCreate,
) -> Any:
    """Register sample record."""
    try:
        sample = await sample_service.create_sample(obj_in=sample_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return SampleRead.model_validate(sample)
    except ExperimentArchivedOrNotFound as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateSampleCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateSampleBarcode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidSampleQuantityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{id}",
    response_model=SampleDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Sample Details",
    description="Fetch sample detail including storage location, type, and chain of custody audit history.",
)
async def get_sample(
    id: UUID,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch sample detail."""
    try:
        sample = await sample_service.get_sample(sample_id=id, tenant_id=current_tenant.id, include_details=True
        )
        return SampleDetail.model_validate(sample)
    except SampleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=SampleRead,
    status_code=status.HTTP_200_OK,
    summary="Update Sample",
    description="Update sample quantity, status, or storage location.",
)
async def update_sample(
    id: UUID,
    *,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    sample_in: SampleUpdate,
) -> Any:
    """Update sample."""
    try:
        sample = await sample_service.update_sample(sample_id=id, obj_in=sample_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return SampleRead.model_validate(sample)
    except SampleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SampleArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidSampleQuantityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Sample",
    description="Soft-delete a sample while preserving chain of custody audit trail.",
)
async def delete_sample(
    id: UUID,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Soft delete sample."""
    try:
        await sample_service.delete_sample(sample_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
    except SampleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{id}/chain-of-custody",
    response_model=List[ChainOfCustodyRead],
    status_code=status.HTTP_200_OK,
    summary="Get Chain of Custody History",
    description="Fetch immutable chain-of-custody audit records for a sample.",
)
async def get_chain_of_custody(
    id: UUID,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch chain of custody history."""
    try:
        coc_list = await sample_service.get_chain_of_custody(sample_id=id, tenant_id=current_tenant.id
        )
        return [ChainOfCustodyRead.model_validate(c) for c in coc_list]
    except SampleNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
