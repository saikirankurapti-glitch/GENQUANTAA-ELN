import math
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

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
)
async def list_sequences(
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    sequence_type: Optional[str] = Query(None, description="Filter by type: DNA, RNA, Protein"),
    status_param: Optional[str] = Query(None, alias="status"),
    experiment_id: Optional[UUID] = Query(None),
    sample_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    try:
        filter_params = SequenceFilter(
            sequence_type=sequence_type,
            status=status_param,
            experiment_id=experiment_id,
            sample_id=sample_id,
            search=search,
        )
        pagination_req = SequencePagination(
            page=page, page_size=page_size, items=[], total=0, total_pages=1
        )
        items, total = await sequence_service.list_sequences(
            tenant_id=current_tenant.id, filters=filter_params, pagination=pagination_req
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return SequenceListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        import logging
        logging.error(f"Error fetching sequences: {e}")
        return SequenceListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.post(
    "/",
    response_model=SequenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Sequence",
)
async def create_sequence(
    *,
    obj_in: SequenceCreate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        seq = await sequence_service.create_sequence(
            obj_in=obj_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return {
            "id": seq.id,
            "tenant_id": seq.tenant_id,
            "organization_id": seq.tenant_id,
            "experiment_id": seq.experiment_id,
            "sample_id": seq.sample_id,
            "sequence_code": f"SEQ-{str(seq.id).split('-')[0].upper()}",
            "sequence_name": seq.name,
            "sequence_type": seq.sequence_type,
            "source": "Unknown",
            "molecular_weight": 0.0,
            "sequence_data": seq.sequence_data,
            "length": seq.length,
            "gc_content": seq.gc_content,
            "status": seq.status,
            "version": 1,
            "metadata_json": {},
            "created_at": seq.created_at,
            "updated_at": seq.updated_at
        }
    except DuplicateSequenceCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidSequenceAlphabet as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{sequence_id}",
    response_model=SequenceDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Sequence Detail",
)
async def get_sequence(
    sequence_id: UUID,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        seq = await sequence_service.get_sequence(
            sequence_id=sequence_id, tenant_id=current_tenant.id
        )
        return {
            "id": seq.id,
            "tenant_id": seq.tenant_id,
            "organization_id": seq.tenant_id,
            "experiment_id": seq.experiment_id,
            "sample_id": seq.sample_id,
            "sequence_code": f"SEQ-{str(seq.id).split('-')[0].upper()}",
            "sequence_name": seq.name,
            "sequence_type": "RNA" if seq.sequence_type.upper() == "MRNA" else ("DNA" if seq.sequence_type.upper() not in ["DNA", "RNA", "PROTEIN"] else seq.sequence_type.upper()),
            "source": "Unknown",
            "molecular_weight": getattr(seq, 'molecular_weight', 0.0),
            "sequence_data": seq.sequence_data,
            "length": seq.length,
            "gc_content": seq.gc_content,
            "status": seq.status,
            "version": 1,
            "metadata_json": {},
            "created_at": seq.created_at,
            "updated_at": seq.updated_at,
            "seq_versions": [],
            "annotations": [],
            "attachments": [],
            "analysis_results": []
        }
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{sequence_id}",
    response_model=SequenceRead,
    status_code=status.HTTP_200_OK,
    summary="Update Sequence",
)
async def update_sequence(
    sequence_id: UUID,
    obj_in: SequenceUpdate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    try:
        seq = await sequence_service.update_sequence(
            sequence_id=sequence_id,
            obj_in=obj_in,
            tenant_id=current_tenant.id,
            current_user=current_user,
        )
        return {
            "id": seq.id,
            "tenant_id": seq.tenant_id,
            "organization_id": seq.tenant_id,
            "experiment_id": seq.experiment_id,
            "sample_id": seq.sample_id,
            "sequence_code": f"SEQ-{str(seq.id).split('-')[0].upper()}",
            "sequence_name": seq.name,
            "sequence_type": seq.sequence_type,
            "source": "Unknown",
            "molecular_weight": 0.0,
            "sequence_data": seq.sequence_data,
            "length": seq.length,
            "gc_content": seq.gc_content,
            "status": seq.status,
            "version": 1,
            "metadata_json": {},
            "created_at": seq.created_at,
            "updated_at": seq.updated_at
        }
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (SequenceArchivedError, InvalidSequenceAlphabet) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{sequence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Sequence",
)
async def delete_sequence(
    sequence_id: UUID,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    try:
        await sequence_service.soft_delete(
            sequence_id=sequence_id, tenant_id=current_tenant.id, current_user=current_user
        )
    except SequenceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
