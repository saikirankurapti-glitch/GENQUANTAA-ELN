import math
from datetime import date
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
    DuplicateInstrumentAssetTag,
    DuplicateInstrumentCode,
    DuplicateInstrumentSerial,
    ExpiredCalibrationReservationError,
    InstrumentNotFound,
    InstrumentNotOperationalError,
    ReservationConflictError,
    ReservationTimeOrderError,
    instrument_service,
)

router = APIRouter()


@router.get(
    "/",
    response_model=InstrumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Instruments",
    description="Fetch paginated instruments for current tenant with filtering and overdue indicators.",
)
async def list_instruments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    instrument_type_id: Optional[UUID] = Query(None),
    operational_status: Optional[str] = Query(None),
    availability_status: Optional[str] = Query(None),
    is_calibration_overdue: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
) -> Any:
    """Paginated instrument listing."""
    filter_params = InstrumentFilter(
        instrument_type_id=instrument_type_id,
        operational_status=operational_status,
        availability_status=availability_status,
        is_calibration_overdue=is_calibration_overdue,
        search=search,
    )
    pagination = InstrumentPagination(
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
    )
    items, total = await instrument_service.list_instruments(
        db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    read_items = []
    today = date.today()
    for item in items:
        read_obj = InstrumentRead.model_validate(item)
        read_obj.is_calibration_overdue = bool(item.calibration_due_date and item.calibration_due_date < today)
        read_obj.is_maintenance_overdue = bool(item.maintenance_due_date and item.maintenance_due_date < today)
        read_items.append(read_obj)

    return InstrumentListResponse(
        items=read_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/search",
    response_model=InstrumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Instruments",
    description="Search instruments by code, serial number, asset tag, or name keyword.",
)
async def search_instruments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """Search instruments."""
    filter_params = InstrumentFilter(search=q)
    pagination = InstrumentPagination(page=page, page_size=page_size)
    items, total = await instrument_service.list_instruments(
        db, tenant_id=current_tenant.id, filter_params=filter_params, pagination=pagination
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    read_items = []
    today = date.today()
    for item in items:
        read_obj = InstrumentRead.model_validate(item)
        read_obj.is_calibration_overdue = bool(item.calibration_due_date and item.calibration_due_date < today)
        read_obj.is_maintenance_overdue = bool(item.maintenance_due_date and item.maintenance_due_date < today)
        read_items.append(read_obj)

    return InstrumentListResponse(
        items=read_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/",
    response_model=InstrumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Instrument",
    description="Register a new laboratory instrument.",
)
async def create_instrument(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    instrument_in: InstrumentCreate,
) -> Any:
    """Create instrument."""
    try:
        instrument = await instrument_service.create_instrument(
            db, obj_in=instrument_in, tenant_id=current_tenant.id, current_user=current_user
        )
        read_obj = InstrumentRead.model_validate(instrument)
        today = date.today()
        read_obj.is_calibration_overdue = bool(instrument.calibration_due_date and instrument.calibration_due_date < today)
        read_obj.is_maintenance_overdue = bool(instrument.maintenance_due_date and instrument.maintenance_due_date < today)
        return read_obj
    except DuplicateInstrumentCode as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateInstrumentSerial as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateInstrumentAssetTag as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{id}",
    response_model=InstrumentDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Instrument Details",
    description="Fetch instrument detail including calibrations, maintenances, reservations, and usage history.",
)
async def get_instrument(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch instrument detail."""
    try:
        instrument = await instrument_service.get_instrument(
            db, instrument_id=id, tenant_id=current_tenant.id, include_details=True
        )
        detail = InstrumentDetail.model_validate(instrument)
        today = date.today()
        detail.is_calibration_overdue = bool(instrument.calibration_due_date and instrument.calibration_due_date < today)
        detail.is_maintenance_overdue = bool(instrument.maintenance_due_date and instrument.maintenance_due_date < today)
        return detail
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{id}",
    response_model=InstrumentRead,
    status_code=status.HTTP_200_OK,
    summary="Update Instrument",
    description="Update instrument configuration or status.",
)
async def update_instrument(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    instrument_in: InstrumentUpdate,
) -> Any:
    """Update instrument."""
    try:
        instrument = await instrument_service.update_instrument(
            db, instrument_id=id, obj_in=instrument_in, tenant_id=current_tenant.id, current_user=current_user
        )
        read_obj = InstrumentRead.model_validate(instrument)
        today = date.today()
        read_obj.is_calibration_overdue = bool(instrument.calibration_due_date and instrument.calibration_due_date < today)
        read_obj.is_maintenance_overdue = bool(instrument.maintenance_due_date and instrument.maintenance_due_date < today)
        return read_obj
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Instrument",
    description="Soft-delete an instrument.",
)
async def delete_instrument(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Soft delete instrument."""
    try:
        await instrument_service.delete_instrument(
            db, instrument_id=id, tenant_id=current_tenant.id, current_user=current_user
        )
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/reserve",
    response_model=InstrumentReservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve Instrument",
    description="Book a time-slot reservation for an instrument.",
)
async def reserve_instrument(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    req: InstrumentReservationCreate,
) -> Any:
    """Reserve instrument."""
    try:
        reservation = await instrument_service.reserve_instrument(
            db, instrument_id=id, req=req, tenant_id=current_tenant.id, current_user=current_user
        )
        return InstrumentReservationRead.model_validate(reservation)
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InstrumentNotOperationalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ReservationTimeOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ExpiredCalibrationReservationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ReservationConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{id}/release",
    status_code=status.HTTP_200_OK,
    summary="Release Reservation",
    description="Cancel/release a reservation booking.",
)
async def release_reservation(
    id: UUID,
    reservation_id: UUID = Query(..., description="Reservation ID to cancel"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Release reservation."""
    try:
        await instrument_service.release_reservation(
            db, reservation_id=reservation_id, tenant_id=current_tenant.id
        )
        return {"detail": "Reservation successfully cancelled."}
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/calibration",
    response_model=InstrumentCalibrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log Calibration",
    description="Record a calibration event for an instrument.",
)
async def add_calibration(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    cal_in: InstrumentCalibrationCreate,
) -> Any:
    """Add calibration."""
    try:
        cal = await instrument_service.add_calibration(
            db, instrument_id=id, cal_in=cal_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return InstrumentCalibrationRead.model_validate(cal)
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/maintenance",
    response_model=InstrumentMaintenanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log Maintenance",
    description="Record a maintenance event for an instrument.",
)
async def add_maintenance(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    maint_in: InstrumentMaintenanceCreate,
) -> Any:
    """Add maintenance."""
    try:
        maint = await instrument_service.add_maintenance(
            db, instrument_id=id, maint_in=maint_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return InstrumentMaintenanceRead.model_validate(maint)
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/usage",
    response_model=InstrumentUsageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log Instrument Usage",
    description="Record an instrument run-time operation log.",
)
async def record_usage(
    id: UUID,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
    usage_in: InstrumentUsageCreate,
) -> Any:
    """Record usage."""
    try:
        usage = await instrument_service.record_usage(
            db, instrument_id=id, usage_in=usage_in, tenant_id=current_tenant.id, current_user=current_user
        )
        return InstrumentUsageRead.model_validate(usage)
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{id}/history",
    response_model=List[InstrumentUsageRead],
    status_code=status.HTTP_200_OK,
    summary="Get Usage History",
    description="Fetch run-time usage history for an instrument.",
)
async def get_usage_history(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch usage history."""
    try:
        history = await instrument_service.list_usage_history(
            db, instrument_id=id, tenant_id=current_tenant.id
        )
        return [InstrumentUsageRead.model_validate(h) for h in history]
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{id}/reservations",
    response_model=List[InstrumentReservationRead],
    status_code=status.HTTP_200_OK,
    summary="Get Reservations",
    description="Fetch all booking reservations for an instrument.",
)
async def get_reservations(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    """Fetch reservations."""
    try:
        reservations = await instrument_service.list_reservations(
            db, instrument_id=id, tenant_id=current_tenant.id
        )
        return [InstrumentReservationRead.model_validate(r) for r in reservations]
    except InstrumentNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
