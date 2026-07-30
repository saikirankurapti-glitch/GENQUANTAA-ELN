from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import crud_tenant
from app.schemas.tenant import Tenant, TenantCreate, TenantUpdate

router = APIRouter()

@router.get("/", response_model=List[Tenant])
async def read_tenants(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve tenants.
    """
    tenants = await crud_tenant.tenant.get_multi(db, skip=skip, limit=limit)
    return tenants

@router.post("/", response_model=Tenant)
async def create_tenant(
    *,
    db: AsyncSession = Depends(deps.get_db),
    tenant_in: TenantCreate,
) -> Any:
    """
    Create new tenant.
    """
    existing = await crud_tenant.tenant.get_by_code(db, code=tenant_in.code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="The tenant with this code already exists in the system.",
        )
    new_tenant = await crud_tenant.tenant.create(db, obj_in=tenant_in)
    return new_tenant

@router.get("/{id}", response_model=Tenant)
async def read_tenant(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: UUID,
) -> Any:
    """
    Get tenant by ID.
    """
    tenant = await crud_tenant.tenant.get(db=db, id=id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/{id}", response_model=Tenant)
async def update_tenant(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: UUID,
    tenant_in: TenantUpdate,
) -> Any:
    """
    Update a tenant.
    """
    tenant = await crud_tenant.tenant.get(db=db, id=id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant = await crud_tenant.tenant.update(db=db, db_obj=tenant, obj_in=tenant_in)
    return tenant

@router.delete("/{id}", response_model=Tenant)
async def delete_tenant(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: UUID,
) -> Any:
    """
    Delete a tenant (Soft Delete).
    """
    tenant = await crud_tenant.tenant.get(db=db, id=id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant = await crud_tenant.tenant.remove(db=db, id=id)
    return tenant
