import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.instrument import (
    Instrument,
    InstrumentAttachment,
    InstrumentCalibration,
    InstrumentMaintenance,
    InstrumentReservation,
    InstrumentType,
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


class InstrumentRepository:
    """Async Repository handling data access for Instrument entities with tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: InstrumentCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Instrument:
        """Create a new Instrument record."""
        instrument = Instrument(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            instrument_type_id=obj_in.instrument_type_id,
            instrument_code=obj_in.instrument_code,
            serial_number=obj_in.serial_number,
            asset_tag=obj_in.asset_tag,
            instrument_name=obj_in.instrument_name,
            manufacturer=obj_in.manufacturer,
            model=obj_in.model,
            location=obj_in.location,
            purchase_date=obj_in.purchase_date,
            installation_date=obj_in.installation_date,
            warranty_expiry=obj_in.warranty_expiry,
            calibration_due_date=obj_in.calibration_due_date,
            maintenance_due_date=obj_in.maintenance_due_date,
            operational_status=obj_in.operational_status,
            availability_status=obj_in.availability_status,
            metadata_json=obj_in.metadata_json,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(instrument)
        await db.commit()
        await db.refresh(instrument)
        return instrument

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Instrument]:
        """Fetch Instrument by ID within tenant scope."""
        stmt = select(Instrument).where(
            Instrument.id == id,
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(Instrument.instrument_type),
                selectinload(Instrument.calibrations),
                selectinload(Instrument.maintenances),
                selectinload(Instrument.reservations),
                selectinload(Instrument.usage_history),
                selectinload(Instrument.attachments),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, instrument_code: str, tenant_id: UUID
    ) -> Optional[Instrument]:
        """Fetch Instrument by code within tenant scope."""
        stmt = select(Instrument).where(
            Instrument.instrument_code == instrument_code.upper(),
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_serial(
        self, db: AsyncSession, *, serial_number: str, tenant_id: UUID
    ) -> Optional[Instrument]:
        """Fetch Instrument by serial number within tenant scope."""
        stmt = select(Instrument).where(
            Instrument.serial_number == serial_number.upper(),
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_asset(
        self, db: AsyncSession, *, asset_tag: str, tenant_id: UUID
    ) -> Optional[Instrument]:
        """Fetch Instrument by asset tag within tenant scope."""
        stmt = select(Instrument).where(
            Instrument.asset_tag == asset_tag.upper(),
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Instrument,
        obj_in: InstrumentUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Instrument:
        """Update existing Instrument attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def archive(
        self, db: AsyncSession, *, instrument_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Instrument]:
        """Archive an Instrument."""
        instrument = await self.get_by_id(db, id=instrument_id, tenant_id=tenant_id)
        if not instrument:
            return None

        instrument.operational_status = "out_of_service"
        instrument.archived_at = datetime.now(timezone.utc)
        instrument.updated_by = current_user_id
        db.add(instrument)
        await db.commit()
        await db.refresh(instrument)
        return instrument

    async def restore(
        self, db: AsyncSession, *, instrument_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Instrument]:
        """Restore an archived Instrument."""
        instrument = await self.get_by_id(db, id=instrument_id, tenant_id=tenant_id)
        if not instrument:
            return None

        instrument.operational_status = "operational"
        instrument.archived_at = None
        instrument.updated_by = current_user_id
        db.add(instrument)
        await db.commit()
        await db.refresh(instrument)
        return instrument

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft delete Instrument."""
        instrument = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not instrument:
            return False

        instrument.is_deleted = True
        instrument.deleted_at = datetime.now(timezone.utc)
        instrument.deleted_by = current_user_id
        db.add(instrument)
        await db.commit()
        return True

    async def list_instruments(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: InstrumentFilter,
        pagination: InstrumentPagination
    ) -> Tuple[List[Instrument], int]:
        """List and search Instruments with filtering and pagination."""
        query = select(Instrument).where(
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )

        if filter_params.instrument_type_id:
            query = query.where(Instrument.instrument_type_id == filter_params.instrument_type_id)
        if filter_params.operational_status:
            query = query.where(Instrument.operational_status == filter_params.operational_status)
        if filter_params.availability_status:
            query = query.where(Instrument.availability_status == filter_params.availability_status)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    Instrument.instrument_code.ilike(pattern),
                    Instrument.serial_number.ilike(pattern),
                    Instrument.asset_tag.ilike(pattern),
                    Instrument.instrument_name.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(Instrument, pagination.sort_by, Instrument.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def add_calibration(
        self, db: AsyncSession, *, instrument_id: UUID, cal_in: InstrumentCalibrationCreate
    ) -> InstrumentCalibration:
        """Add a calibration record and update instrument calibration_due_date."""
        calibration = InstrumentCalibration(
            instrument_id=instrument_id,
            calibration_date=cal_in.calibration_date,
            calibrated_by=cal_in.calibrated_by,
            certificate_number=cal_in.certificate_number,
            result=cal_in.result,
            remarks=cal_in.remarks,
            next_due_date=cal_in.next_due_date,
        )
        db.add(calibration)

        # Update Instrument next due date
        instrument = await db.get(Instrument, instrument_id)
        if instrument and cal_in.next_due_date:
            instrument.calibration_due_date = cal_in.next_due_date
            db.add(instrument)

        await db.commit()
        await db.refresh(calibration)
        return calibration

    async def add_maintenance(
        self, db: AsyncSession, *, instrument_id: UUID, maint_in: InstrumentMaintenanceCreate
    ) -> InstrumentMaintenance:
        """Add a maintenance record and update instrument maintenance_due_date."""
        maintenance = InstrumentMaintenance(
            instrument_id=instrument_id,
            maintenance_type=maint_in.maintenance_type,
            maintenance_date=maint_in.maintenance_date,
            engineer=maint_in.engineer,
            vendor=maint_in.vendor,
            remarks=maint_in.remarks,
            next_due_date=maint_in.next_due_date,
        )
        db.add(maintenance)

        instrument = await db.get(Instrument, instrument_id)
        if instrument and maint_in.next_due_date:
            instrument.maintenance_due_date = maint_in.next_due_date
            db.add(instrument)

        await db.commit()
        await db.refresh(maintenance)
        return maintenance

    async def has_reservation_conflict(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if an overlapping confirmed reservation exists for the time interval."""
        stmt = select(InstrumentReservation).where(
            InstrumentReservation.instrument_id == instrument_id,
            InstrumentReservation.status == "confirmed",
            and_(
                InstrumentReservation.start_time < end_time,
                InstrumentReservation.end_time > start_time,
            )
        )
        if exclude_id:
            stmt = stmt.where(InstrumentReservation.id != exclude_id)

        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def reserve_instrument(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        res_in: InstrumentReservationCreate,
        reserver_id: UUID
    ) -> InstrumentReservation:
        """Create a new reservation booking."""
        reservation = InstrumentReservation(
            instrument_id=instrument_id,
            experiment_id=res_in.experiment_id,
            reserved_by=reserver_id,
            start_time=res_in.start_time,
            end_time=res_in.end_time,
            status="confirmed",
        )
        db.add(reservation)
        await db.commit()
        await db.refresh(reservation)
        return reservation

    async def release_reservation(
        self, db: AsyncSession, *, reservation_id: UUID
    ) -> bool:
        """Cancel/release an existing reservation."""
        res = await db.get(InstrumentReservation, reservation_id)
        if not res:
            return False

        res.status = "cancelled"
        db.add(res)
        await db.commit()
        return True

    async def record_usage(
        self,
        db: AsyncSession,
        *,
        instrument_id: UUID,
        usage_in: InstrumentUsageCreate,
        operator_id: UUID
    ) -> InstrumentUsage:
        """Record an instrument run-time operation log."""
        usage = InstrumentUsage(
            instrument_id=instrument_id,
            experiment_id=usage_in.experiment_id,
            protocol_id=usage_in.protocol_id,
            operator_id=operator_id,
            usage_start=usage_in.usage_start,
            usage_end=usage_in.usage_end,
            remarks=usage_in.remarks,
        )
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
        return usage

    async def list_reservations(
        self, db: AsyncSession, *, instrument_id: UUID
    ) -> List[InstrumentReservation]:
        """Fetch reservations for an instrument."""
        stmt = (
            select(InstrumentReservation)
            .where(InstrumentReservation.instrument_id == instrument_id)
            .order_by(InstrumentReservation.start_time.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def list_usage_history(
        self, db: AsyncSession, *, instrument_id: UUID
    ) -> List[InstrumentUsage]:
        """Fetch run-time usage logs for an instrument."""
        stmt = (
            select(InstrumentUsage)
            .where(InstrumentUsage.instrument_id == instrument_id)
            .order_by(InstrumentUsage.usage_start.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


instrument_repo = InstrumentRepository()
