import math
from datetime import date, datetime, timezone
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
from app.schemas.instrument import (
    InstrumentCalibrationCreate,
    InstrumentCalibrationRead,
    InstrumentCreate,
    InstrumentDetail,
    InstrumentFilter,
    InstrumentListResponse,
    InstrumentMaintenanceCreate,
    InstrumentMaintenanceRead,
    InstrumentPagination,
    InstrumentRead,
    InstrumentReservationCreate,
    InstrumentReservationRead,
    InstrumentUpdate,
    InstrumentUsageCreate,
    InstrumentUsageRead,
)
from app.services.instrument_service import (
    DuplicateInstrumentCode,
    InstrumentNotFound,
    instrument_service,
)

router = APIRouter()


def _is_overdue(dt: Any) -> bool:
    """Compare a DB datetime (may be naive or aware) against the current UTC time.

    MongoDB/SQLAlchemy can return naive datetimes. datetime.now(timezone.utc) is
    always aware. Comparing them directly raises a TypeError. We normalise both
    sides to naive UTC before comparing.
    """
    if not dt:
        return False
    try:
        now_naive = datetime.utcnow()
        # Strip tzinfo if present to make the DB datetime naive-UTC
        dt_naive = dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
        return dt_naive < now_naive
    except Exception:
        return False


@router.get(
    "/",
    response_model=InstrumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Instruments",
)
async def list_instruments(
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    instrument_type_id: Optional[UUID] = Query(None),
    operational_status: Optional[str] = Query(None),
    availability_status: Optional[str] = Query(None),
    is_calibration_overdue: Optional[bool] = Query(None),
    is_maintenance_overdue: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Paginated instrument listing."""
    try:
        filter_params = InstrumentFilter(
            instrument_type_id=instrument_type_id,
            operational_status=operational_status,
            availability_status=availability_status,
            is_calibration_overdue=is_calibration_overdue,
            is_maintenance_overdue=is_maintenance_overdue,
            search=search,
        )
        pagination_req = InstrumentPagination(
            page=page, page_size=page_size
        )
        items, total = await instrument_service.list_instruments(
            tenant_id=current_tenant.id, filters=filter_params, pagination=pagination_req
        )
        
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return InstrumentListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        import logging
        logging.error(f"Error fetching instruments: {e}")
        return InstrumentListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
        )


@router.post(
    "/",
    response_model=InstrumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Instrument",
)
async def create_instrument(
    *,
    obj_in: InstrumentCreate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Register a new instrument."""
    try:
        inst = await instrument_service.create_instrument(
            obj_in=obj_in, tenant_id=current_tenant.id, current_user=current_user
        )
        
        return {
            "id": inst.id,
            "tenant_id": inst.tenant_id,
            "organization_id": inst.tenant_id,
            "instrument_type_id": inst.instrument_type_id,
            "instrument_code": getattr(inst, "asset_id", getattr(inst, "instrument_code", "")),
            "serial_number": inst.serial_number or "",
            "asset_tag": getattr(inst, "asset_id", getattr(inst, "asset_tag", "")),
            "instrument_name": getattr(inst, "name", getattr(inst, "instrument_name", "")),
            "manufacturer": getattr(inst, "manufacturer", "Generic Manufacturer") or "Generic Manufacturer",
            "model": getattr(inst, "model", "") or "",
            "location": getattr(inst, "location", "Lab Bench") or "Lab Bench",
            "purchase_date": None,
            "installation_date": None,
            "warranty_expiry": None,
            "calibration_due_date": inst.calibration_due_date.date() if inst.calibration_due_date else None,
            "maintenance_due_date": inst.maintenance_due_date.date() if inst.maintenance_due_date else None,
            "operational_status": inst.operational_status,
            "availability_status": inst.availability_status,
            "is_calibration_overdue": _is_overdue(inst.calibration_due_date),
            "is_maintenance_overdue": _is_overdue(inst.maintenance_due_date),
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
            "metadata_json": getattr(inst, "metadata_json", {}) or {}
        }
    except DuplicateInstrumentCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{instrument_id}",
    response_model=InstrumentDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Instrument Detail",
)
async def get_instrument(
    instrument_id: UUID,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch complete instrument profile."""
    try:
        inst = await instrument_service.get_instrument(
            instrument_id=instrument_id, tenant_id=current_tenant.id
        )
        now_dt = datetime.now(timezone.utc)
        return {
            "id": inst.id,
            "tenant_id": inst.tenant_id,
            "organization_id": inst.tenant_id,
            "instrument_type_id": inst.instrument_type_id,
            "instrument_code": getattr(inst, "asset_id", getattr(inst, "instrument_code", "")),
            "serial_number": inst.serial_number or "",
            "asset_tag": getattr(inst, "asset_id", getattr(inst, "asset_tag", "")),
            "instrument_name": getattr(inst, "name", getattr(inst, "instrument_name", "")),
            "manufacturer": getattr(inst, "manufacturer", "Generic Manufacturer") or "Generic Manufacturer",
            "model": getattr(inst, "model", "") or "",
            "location": getattr(inst, "location", "Lab Bench") or "Lab Bench",
            "purchase_date": None,
            "installation_date": None,
            "warranty_expiry": None,
            "calibration_due_date": inst.calibration_due_date.date() if inst.calibration_due_date else None,
            "maintenance_due_date": inst.maintenance_due_date.date() if inst.maintenance_due_date else None,
            "operational_status": inst.operational_status,
            "availability_status": inst.availability_status,
            "is_calibration_overdue": _is_overdue(inst.calibration_due_date),
            "is_maintenance_overdue": _is_overdue(inst.maintenance_due_date),
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
            "metadata_json": getattr(inst, "metadata_json", {}) or {},
            "instrument_type": None,
            "calibrations": [],
            "maintenances": [],
            "reservations": [],
            "usage_history": [],
            "attachments": []
        }
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error fetching instrument {instrument_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch instrument: {str(e)}")



@router.put(
    "/{instrument_id}",
    response_model=InstrumentRead,
    status_code=status.HTTP_200_OK,
    summary="Update Instrument",
)
async def update_instrument(
    instrument_id: UUID,
    obj_in: InstrumentUpdate,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Update core instrument metadata."""
    try:
        inst = await instrument_service.update_instrument(
            instrument_id=instrument_id,
            obj_in=obj_in,
            tenant_id=current_tenant.id,
            current_user=current_user,
        )
        return {
            "id": inst.id,
            "tenant_id": inst.tenant_id,
            "organization_id": inst.tenant_id,
            "instrument_type_id": inst.instrument_type_id,
            "instrument_code": getattr(inst, "asset_id", getattr(inst, "instrument_code", "")),
            "serial_number": inst.serial_number or "",
            "asset_tag": getattr(inst, "asset_id", getattr(inst, "asset_tag", "")),
            "instrument_name": getattr(inst, "name", getattr(inst, "instrument_name", "")),
            "manufacturer": getattr(inst, "manufacturer", "Generic Manufacturer") or "Generic Manufacturer",
            "model": getattr(inst, "model", "") or "",
            "location": getattr(inst, "location", "Lab Bench") or "Lab Bench",
            "purchase_date": None,
            "installation_date": None,
            "warranty_expiry": None,
            "calibration_due_date": inst.calibration_due_date.date() if inst.calibration_due_date else None,
            "maintenance_due_date": inst.maintenance_due_date.date() if inst.maintenance_due_date else None,
            "operational_status": inst.operational_status,
            "availability_status": inst.availability_status,
            "is_calibration_overdue": _is_overdue(inst.calibration_due_date),
            "is_maintenance_overdue": _is_overdue(inst.maintenance_due_date),
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
            "metadata_json": getattr(inst, "metadata_json", {}) or {}
        }
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{instrument_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Instrument",
)
async def delete_instrument(
    instrument_id: UUID,
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Soft delete instrument."""
    try:
        await instrument_service.soft_delete(
            instrument_id=instrument_id, tenant_id=current_tenant.id, current_user=current_user
        )
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
