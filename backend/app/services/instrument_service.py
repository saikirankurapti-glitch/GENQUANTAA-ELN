import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_instrument import instrument_repo
from app.models.identity import User
from app.models.instrument import (
    Instrument,
    InstrumentCalibration,
    InstrumentMaintenance,
    InstrumentReservation,
    InstrumentUsage,
)
from app.schemas.instrument import (
    InstrumentCalibrationCreate,
    InstrumentCreate,
    InstrumentFilter,
    InstrumentMaintenanceCreate,
    InstrumentPagination,
    InstrumentReservationCreate,
    InstrumentUpdate,
    InstrumentUsageCreate,
)

logger = logging.getLogger(__name__)


# Domain Exceptions
class InstrumentNotFound(Exception):
    pass


class DuplicateInstrumentCode(Exception):
    pass


class DuplicateInstrumentSerial(Exception):
    pass


class DuplicateInstrumentAssetTag(Exception):
    pass


class InstrumentNotOperationalError(Exception):
    pass


class ReservationConflictError(Exception):
    pass


class ExpiredCalibrationReservationError(Exception):
    pass


class ReservationTimeOrderError(Exception):
    pass


class InstrumentService:
    """Service layer enforcing instrument reservation rules, calibration checks, and uniqueness constraints."""

    async def create_instrument(
        self, db: AsyncSession, *, obj_in: InstrumentCreate, tenant_id: UUID, current_user: User
    ) -> Instrument:
        """Register a new instrument validating uniqueness of code, serial number, and asset tag."""
        # 1. Validate Code Uniqueness
        if await instrument_repo.get_by_code(db, instrument_code=obj_in.instrument_code, tenant_id=tenant_id):
            raise DuplicateInstrumentCode(
                f"Instrument code '{obj_in.instrument_code}' already exists in this tenant workspace."
            )

        # 2. Validate Serial Number Uniqueness
        if await instrument_repo.get_by_serial(db, serial_number=obj_in.serial_number, tenant_id=tenant_id):
            raise DuplicateInstrumentSerial(
                f"Serial number '{obj_in.serial_number}' already exists in this tenant workspace."
            )

        # 3. Validate Asset Tag Uniqueness
        if await instrument_repo.get_by_asset(db, asset_tag=obj_in.asset_tag, tenant_id=tenant_id):
            raise DuplicateInstrumentAssetTag(
                f"Asset tag '{obj_in.asset_tag}' already exists in this tenant workspace."
            )

        instrument = await instrument_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"InstrumentService: Registered instrument '{instrument.instrument_code}' (ID: {instrument.id})")
        return instrument

    async def get_instrument(
        self, db: AsyncSession, *, instrument_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Instrument:
        """Fetch instrument by ID or raise InstrumentNotFound."""
        instrument = await instrument_repo.get_by_id(
            db, id=instrument_id, tenant_id=tenant_id, include_details=include_details
        )
        if not instrument:
            raise InstrumentNotFound(f"Instrument {instrument_id} not found.")
        return instrument

    async def update_instrument(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        obj_in: InstrumentUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Instrument:
        """Update instrument attributes."""
        instrument = await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id)
        updated = await instrument_repo.update(
            db, db_obj=instrument, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"InstrumentService: Updated instrument {instrument_id}")
        return updated

    async def reserve_instrument(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        req: InstrumentReservationCreate,
        tenant_id: UUID,
        current_user: User
    ) -> InstrumentReservation:
        """Reserve an instrument checking operational status, calibration validity, and time conflict."""
        instrument = await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id)

        # 1. Check Operational Status
        if instrument.operational_status != "operational":
            raise InstrumentNotOperationalError(
                f"Cannot reserve instrument {instrument.instrument_code} in status '{instrument.operational_status}'."
            )

        # 2. Check Time Order
        if req.end_time <= req.start_time:
            raise ReservationTimeOrderError("Reservation end time must be after start time.")

        # 3. Check Calibration Expiry
        if instrument.calibration_due_date and instrument.calibration_due_date < date.today():
            raise ExpiredCalibrationReservationError(
                f"Cannot reserve instrument {instrument.instrument_code} with overdue calibration (due: {instrument.calibration_due_date})."
            )

        # 4. Check Reservation Conflict
        conflict = await instrument_repo.has_reservation_conflict(
            db, instrument_id=instrument_id, start_time=req.start_time, end_time=req.end_time
        )
        if conflict:
            raise ReservationConflictError("Selected reservation time slot overlaps with an existing booking.")

        reservation = await instrument_repo.reserve_instrument(
            db, instrument_id=instrument_id, res_in=req, reserver_id=current_user.id
        )
        logger.info(f"InstrumentService: Reserved instrument {instrument_id} for user {current_user.id}")
        return reservation

    async def release_reservation(
        self, db: AsyncSession, *, reservation_id: UUID, tenant_id: UUID
    ) -> bool:
        """Release/cancel an existing reservation booking."""
        success = await instrument_repo.release_reservation(db, reservation_id=reservation_id)
        if not success:
            raise InstrumentNotFound("Reservation not found.")
        return True

    async def add_calibration(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        cal_in: InstrumentCalibrationCreate,
        tenant_id: UUID,
        current_user: User
    ) -> InstrumentCalibration:
        """Log a calibration event and update next due date."""
        await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id)
        return await instrument_repo.add_calibration(db, instrument_id=instrument_id, cal_in=cal_in)

    async def add_maintenance(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        maint_in: InstrumentMaintenanceCreate,
        tenant_id: UUID,
        current_user: User
    ) -> InstrumentMaintenance:
        """Log a maintenance event and update next due date."""
        await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id)
        return await instrument_repo.add_maintenance(db, instrument_id=instrument_id, maint_in=maint_in)

    async def record_usage(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        usage_in: InstrumentUsageCreate,
        tenant_id: UUID,
        current_user: User
    ) -> InstrumentUsage:
        """Log instrument run-time operation."""
        await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id)
        return await instrument_repo.record_usage(
            db, instrument_id=instrument_id, usage_in=usage_in, operator_id=current_user.id
        )

    async def delete_instrument(
        self, db: AsyncSession, *, instrument_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete an instrument."""
        success = await instrument_repo.soft_delete(
            db, id=instrument_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise InstrumentNotFound(f"Instrument {instrument_id} not found.")
        logger.info(f"InstrumentService: Soft deleted instrument {instrument_id}")
        return True

    async def list_instruments(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: InstrumentFilter,
        pagination: InstrumentPagination
    ) -> Tuple[List[Instrument], int]:
        """List instruments with filtering and pagination."""
        return await instrument_repo.list_instruments(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

    async def list_reservations(
        self, db: AsyncSession, *, instrument_id: UUID, tenant_id: UUID
    ) -> List[InstrumentReservation]:
        """Fetch reservations for an instrument."""
        await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id, include_details=False)
        return await instrument_repo.list_reservations(db, instrument_id=instrument_id)

    async def list_usage_history(
        self, db: AsyncSession, *, instrument_id: UUID, tenant_id: UUID
    ) -> List[InstrumentUsage]:
        """Fetch run-time usage logs for an instrument."""
        await self.get_instrument(db, instrument_id=instrument_id, tenant_id=tenant_id, include_details=False)
        return await instrument_repo.list_usage_history(db, instrument_id=instrument_id)


instrument_service = InstrumentService()
