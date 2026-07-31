import math
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security.authorization import (
    get_current_active_user,
    get_current_tenant,
    require_permission,
)
from app.db.enums import ProjectStatus
from app.models.identity import User
from app.models.tenant import Tenant
from app.schemas.project import (
    ProjectArchiveRequest,
    ProjectCollaboratorCreate,
    ProjectCollaboratorRead,
    ProjectCreate,
    ProjectDetail,
    ProjectFilter,
    ProjectListResponse,
    ProjectPagination,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import (
    DuplicateProjectCode,
    InvalidStatusTransition,
    ProjectArchivedError,
    ProjectNotFound,
    project_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Projects",
    description="Fetch paginated projects for current tenant with filtering and sorting.",
)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    status_param: Optional[ProjectStatus] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    owner_id: Optional[UUID] = Query(None),
    is_archived: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    """Paginated project listing."""
    try:
        filter_params = ProjectFilter(
            status=status_param,
            priority=priority,
            owner_id=owner_id,
            is_archived=is_archived,
            search=search,
        )
        pagination = ProjectPagination(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )
        items, total = await project_service.list_projects(
            db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return ProjectListResponse(
            items=[ProjectRead.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ProjectListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.get(
    "/search",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Projects",
    description="Search projects by code, name, or description query.",
)
async def search_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search term"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search projects."""
    try:
        filter_params = ProjectFilter(search=q)
        pagination = ProjectPagination(page=page, page_size=page_size)
        items, total = await project_service.list_projects(
            db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return ProjectListResponse(
            items=[ProjectRead.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        return ProjectListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Create a new research project within tenant scope.",
)
async def create_project(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    project_in: ProjectCreate,
) -> Any:
    """Create project record."""
    try:
        project = await project_service.create_project(
            db, obj_in=project_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProjectRead.model_validate(project)
    except DuplicateProjectCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Create project error: {str(e)}\n{tb}")


@router.get(
    "/{id}",
    response_model=ProjectDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
    description="Fetch project by ID including collaborators and attachments.",
)
async def get_project(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch project detail."""
    try:
        project = await project_service.get_project(
            db, project_id=id, tenant_id=current_tenant.id, include_details=True
        )
        return ProjectDetail.model_validate(project)
    except ProjectNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Update Project",
    description="Update project details.",
)
async def update_project(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    project_in: ProjectUpdate,
) -> Any:
    """Update project."""
    try:
        project = await project_service.update_project(
            db, project_id=id, obj_in=project_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProjectRead.model_validate(project)
    except ProjectNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProjectArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidStatusTransition as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
    description="Soft-delete a project while preserving audit trail.",
)
async def delete_project(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Soft delete project."""
    try:
        await project_service.delete_project(
            db, project_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
    except ProjectNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/archive",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Archive Project",
    description="Archive a project.",
)
async def archive_project(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Archive project."""
    try:
        project = await project_service.archive_project(
            db, project_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProjectRead.model_validate(project)
    except ProjectNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/restore",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Restore Project",
    description="Restore an archived project back to active status.",
)
async def restore_project(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Restore project."""
    try:
        project = await project_service.restore_project(
            db, project_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
        return ProjectRead.model_validate(project)
    except ProjectNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/collaborators",
    response_model=ProjectCollaboratorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Collaborator",
    description="Assign a collaborator user to a project.",
)
async def add_collaborator(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    collab_in: ProjectCollaboratorCreate,
) -> Any:
    """Add project collaborator."""
    try:
        collab = await project_service.add_collaborator(
            db,
            project_id=id,
            user_id=collab_in.user_id,
            role=collab_in.role,
            tenant_id=current_tenant.id,
            current_user=current_user,
        )
        return ProjectCollaboratorRead.model_validate(collab)
    except ProjectNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProjectArchivedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
