import math
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import get_current_active_user, get_current_tenant
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.sequence import (
    FastaUploadResponse,
    SequenceAnnotationCreate,
    SequenceAnnotationRead,
    SequenceAnalysisResultRead,
    SequenceCreate,
    SequenceDetail,
    SequenceFilter,
    SequenceListResponse,
    SequencePagination,
    SequenceRead,
    SequenceUpdate,
)
from app.services.sequence_service import (
    DuplicateSequenceCode,
    InvalidSequenceAlphabet,
    SequenceArchivedError,
    SequenceNotFound,
    sequence_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=SequenceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Sequences",
    description="Paginated list of DNA, RNA, and Protein sequences for the current tenant.",
)
async def list_sequences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    sequence_type: Optional[str] = Query(None, description="Filter by type: DNA, RNA, Protein"),
    status_param: Optional[str] = Query(None, alias="status"),
    experiment_id: Optional[UUID] = Query(None),
    sample_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    filter_params = SequenceFilter(
        sequence_type=sequence_type,
        status=status_param,
        experiment_id=experiment_id,
        sample_id=sample_id,
        search=search,
    )
    pagination = SequencePagination(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    items, total = await sequence_service.list_sequences(
        db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return SequenceListResponse(
        items=[SequenceRead.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/search",
    response_model=SequenceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Sequences",
    description="Search sequences by code or name keyword.",
)
async def search_sequences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    filter_params = SequenceFilter(search=q)
    pagination = SequencePagination(page=page, page_size=page_size)
    items, total = await sequence_service.list_sequences(
        db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return SequenceListResponse(
        items=[SequenceRead.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/upload-fasta",
    response_model=FastaUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload FASTA",
    description="Parse and bulk-register sequences from a FASTA-formatted text body.",
)
async def upload_fasta(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    fasta_text: str = Body(..., media_type="text/plain", description="Raw FASTA content"),
    sequence_type: str = Query(..., description="DNA, RNA, or Protein"),
    organization_id: UUID = Query(..., description="Organization ID to register under"),
    experiment_id: Optional[UUID] = Query(None),
    sample_id: Optional[UUID] = Query(None),
) -> Any:
    return await sequence_service.upload_fasta(
        db,
        fasta_text=fasta_text,
        sequence_type=sequence_type,
        organization_id=organization_id,
        tenant_id=current_tenant.id,
        current_user=current_user,
        experiment_id=experiment_id,
        sample_id=sample_id,
    )


@router.post(
    "/",
    response_model=SequenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Sequence",
    description="Register a new DNA, RNA, or Protein sequence with biological validation.",
)
async def create_sequence(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    seq_in: SequenceCreate,
) -> Any:
    try:
        seq = await sequence_service.create_sequence(
            db, obj_in=seq_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return SequenceRead.model_validate(seq)
    except DuplicateSequenceCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidSequenceAlphabet as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{id}",
    response_model=SequenceDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Sequence Detail",
    description="Fetch a sequence with full version history, annotations, attachments, and analysis results.",
)
async def get_sequence(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        seq = await sequence_service.get_sequence(
            db, sequence_id=id, tenant_id=current_tenant.id, include_details=True
        )
        return SequenceDetail.model_validate(seq)
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=SequenceRead,
    status_code=status.HTTP_200_OK,
    summary="Update Sequence",
    description="Update sequence data or metadata. Sequence data changes are versioned automatically.",
)
async def update_sequence(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    seq_in: SequenceUpdate,
) -> Any:
    try:
        seq = await sequence_service.update_sequence(
            db, sequence_id=id, obj_in=seq_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return SequenceRead.model_validate(seq)
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SequenceArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidSequenceAlphabet as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Sequence",
    description="Soft-delete a sequence record.",
)
async def delete_sequence(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    try:
        await sequence_service.delete_sequence(
            db, sequence_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/annotations",
    response_model=SequenceAnnotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Annotation",
    description="Annotate a specific region (e.g. ORF, promoter, CDS) of a sequence.",
)
async def add_annotation(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    ann_in: SequenceAnnotationCreate,
) -> Any:
    try:
        ann = await sequence_service.add_annotation(
            db, sequence_id=id, ann_in=ann_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return SequenceAnnotationRead.model_validate(ann)
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{id}/analysis",
    response_model=List[SequenceAnalysisResultRead],
    status_code=status.HTTP_200_OK,
    summary="Get Analysis Results",
    description="Fetch all external analysis results (BLAST, ORF, secondary structure) for a sequence.",
)
async def get_analysis_results(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        results = await sequence_service.list_analysis_results(
            db, sequence_id=id, tenant_id=current_tenant.id
        )
        return [SequenceAnalysisResultRead.model_validate(r) for r in results]
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
