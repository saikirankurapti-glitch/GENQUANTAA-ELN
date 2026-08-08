import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

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


class InstrumentService:
    """Service layer enforcing instrument lifecycle, calibration tracking, and scheduling conflict prevention."""

    async def create_instrument(
        self, *, obj_in: InstrumentCreate, tenant_id: UUID, current_user: User
    ) -> Instrument:
        """Create a new instrument ensuring code, serial, and asset_tag uniqueness per tenant."""
        existing = await instrument_repo.get_by_code(instrument_code=obj_in.instrument_code, tenant_id=tenant_id)
        if existing:
            raise DuplicateInstrumentCode(f"Instrument code '{obj_in.instrument_code}' is already in use.")

        inst = await instrument_repo.create(
            obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"InstrumentService: Created instrument {inst.id}")
        return inst

    async def get_instrument(
        self, *, instrument_id: UUID, tenant_id: UUID
    ) -> Instrument:
        """Retrieve instrument with full detail graph."""
        inst = await instrument_repo.get_by_id(
            id=instrument_id, tenant_id=tenant_id, include_details=True
        )
        if not inst:
            raise InstrumentNotFound(f"Instrument ID {instrument_id} not found.")
        return inst

    async def update_instrument(
        self,
        *,
        instrument_id: UUID,
        obj_in: InstrumentUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Instrument:
        """Update core instrument metadata and re-evaluate operational status if overridden."""
        inst = await self.get_instrument(instrument_id=instrument_id, tenant_id=tenant_id)
        updated_inst = await instrument_repo.update(
            db_obj=inst, obj_in=obj_in, current_user_id=current_user.id
        )
        return updated_inst

    async def soft_delete(
        self, *, instrument_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        success = await instrument_repo.soft_delete(
            id=instrument_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise InstrumentNotFound(f"Instrument ID {instrument_id} not found.")
        logger.info(f"InstrumentService: Soft deleted instrument {instrument_id}")
        return True

    async def list_instruments(
        self, *, tenant_id: UUID, filters: InstrumentFilter, pagination: InstrumentPagination
    ) -> Tuple[List[dict], int]:
        return await instrument_repo.get_multi(
            tenant_id=tenant_id,
            instrument_type_id=filters.instrument_type_id,
            operational_status=filters.operational_status,
            availability_status=filters.availability_status,
            is_calibration_overdue=filters.is_calibration_overdue,
            is_maintenance_overdue=filters.is_maintenance_overdue,
            search=filters.search,
            skip=(pagination.page - 1) * pagination.page_size,
            limit=pagination.page_size,
        )


instrument_service = InstrumentService()
