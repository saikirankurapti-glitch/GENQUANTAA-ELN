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
from app.schemas.notebook import (
    NotebookAttachmentRead,
    NotebookCommentCreate,
    NotebookCommentRead,
    NotebookEntryCreate,
    NotebookEntryDetail,
    NotebookEntryRead,
    NotebookEntryUpdate,
    NotebookEntryVersionRead,
    NotebookFilter,
    NotebookListResponse,
    NotebookPagination,
    NotebookTagCreate,
    NotebookTagRead,
)
from app.services.notebook_service import (
    DuplicateNotebookEntryNumber,
    ExperimentArchivedOrNotFound,
    InvalidAttachmentError,
    NotebookEntryLockedError,
    NotebookEntryNotFound,
    notebook_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=NotebookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Notebook Entries",
    description="Fetch paginated notebook entries for current tenant with filtering and sorting.",
)
async def list_notebook_entries(    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    experiment_id: Optional[UUID] = Query(None),
    entry_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    """Paginated notebook entry listing."""
    try:
        filter_params = NotebookFilter(
            experiment_id=experiment_id, entry_type=entry_type, search=search
        )
        pagination = NotebookPagination(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items, total = await notebook_service.list_entries(tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return NotebookListResponse(
            items=[NotebookEntryRead.model_validate(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        return NotebookListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.get(
    "/search",
    response_model=NotebookListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Notebook Entries",
    description="Search notebook entries by title or content query.",
)
async def search_notebook_entries(    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search notebook entries."""
    try:
        filter_params = NotebookFilter(search=q)
        pagination = NotebookPagination(page=page, page_size=page_size)
        items, total = await notebook_service.list_entries(tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return NotebookListResponse(
            items=[NotebookEntryRead.model_validate(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        return NotebookListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.post(
    "/",
    response_model=NotebookEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Notebook Entry",
    description="Create a new notebook entry and initial Version 1 snapshot.",
)
async def create_notebook_entry(
    *,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    entry_in: NotebookEntryCreate,
) -> Any:
    """Create notebook entry."""
    try:
        entry = await notebook_service.create_entry(obj_in=entry_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return NotebookEntryRead.model_validate(entry)
    except ExperimentArchivedOrNotFound as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateNotebookEntryNumber as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{id}",
    response_model=NotebookEntryDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Notebook Entry Details",
    description="Fetch notebook entry detail including versions, comments, tags, and attachments.",
)
async def get_notebook_entry(
    id: UUID,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch notebook entry detail."""
    try:
        entry = await notebook_service.get_entry(entry_id=id, tenant_id=current_tenant.id, include_details=True
        )
        return NotebookEntryDetail.model_validate(entry)
    except NotebookEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=NotebookEntryRead,
    status_code=status.HTTP_200_OK,
    summary="Update Notebook Entry",
    description="Update entry content, incrementing current_version and storing a new immutable version snapshot.",
)
async def update_notebook_entry(
    id: UUID,
    *,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    entry_in: NotebookEntryUpdate,
) -> Any:
    """Update notebook entry."""
    try:
        entry, _ = await notebook_service.update_entry(entry_id=id, obj_in=entry_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return NotebookEntryRead.model_validate(entry)
    except NotebookEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotebookEntryLockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{id}/versions",
    response_model=List[NotebookEntryVersionRead],
    status_code=status.HTTP_200_OK,
    summary="Get Version History",
    description="Fetch all historical version snapshots for a notebook entry.",
)
async def get_version_history(
    id: UUID,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch version history."""
    try:
        versions = await notebook_service.list_versions(entry_id=id, tenant_id=current_tenant.id
        )
        return [NotebookEntryVersionRead.model_validate(v) for v in versions]
    except NotebookEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/comments",
    response_model=NotebookCommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Comment",
    description="Post a comment or reply on a notebook entry.",
)
async def add_comment(
    id: UUID,
    *,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    comment_in: NotebookCommentCreate,
) -> Any:
    """Add comment."""
    try:
        comment = await notebook_service.add_comment(entry_id=id, obj_in=comment_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return NotebookCommentRead.model_validate(comment)
    except NotebookEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/tags",
    response_model=NotebookTagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Tag",
    description="Attach a color-coded tag to a notebook entry.",
)
async def add_tag(
    id: UUID,
    *,    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    tag_in: NotebookTagCreate,
) -> Any:
    """Add tag."""
    try:
        tag = await notebook_service.add_tag(entry_id=id, obj_in=tag_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return NotebookTagRead.model_validate(tag)
    except NotebookEntryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
