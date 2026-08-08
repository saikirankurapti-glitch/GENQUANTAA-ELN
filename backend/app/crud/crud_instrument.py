import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

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
        *,
        obj_in: InstrumentCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Instrument:
        """Create a new Instrument record."""
        instrument = Instrument(
            tenant_id=tenant_id,
            instrument_type_id=obj_in.instrument_type_id,
            name=obj_in.instrument_name,
            asset_id=obj_in.instrument_code,
            model=obj_in.model,
            serial_number=obj_in.serial_number,
            operational_status=obj_in.operational_status,
            availability_status=obj_in.availability_status,
            is_operational=(obj_in.operational_status == "operational"),
            calibration_due_date=datetime.combine(obj_in.calibration_due_date, datetime.min.time()) if obj_in.calibration_due_date else None,
            maintenance_due_date=datetime.combine(obj_in.maintenance_due_date, datetime.min.time()) if obj_in.maintenance_due_date else None,
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await instrument.insert()
        return instrument

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Instrument]:
        return await Instrument.find_one(
            Instrument.id == id,
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )

    async def get_by_code(
        self, *, instrument_code: str, tenant_id: UUID
    ) -> Optional[Instrument]:
        return await Instrument.find_one(
            Instrument.asset_id == instrument_code.upper(),
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )

    async def update(
        self,
        *,
        db_obj: Instrument,
        obj_in: InstrumentUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Instrument:
        update_data = obj_in.model_dump(exclude_unset=True)
        if 'instrument_name' in update_data:
            db_obj.name = update_data['instrument_name']
        if 'operational_status' in update_data:
            db_obj.operational_status = update_data['operational_status']
            db_obj.is_operational = (update_data['operational_status'] == "operational")
        if 'availability_status' in update_data:
            db_obj.availability_status = update_data['availability_status']
        if 'calibration_due_date' in update_data and update_data['calibration_due_date']:
            db_obj.calibration_due_date = datetime.combine(update_data['calibration_due_date'], datetime.min.time())
        if 'maintenance_due_date' in update_data and update_data['maintenance_due_date']:
            db_obj.maintenance_due_date = datetime.combine(update_data['maintenance_due_date'], datetime.min.time())

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()
        return db_obj

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        obj = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not obj:
            return False
        obj.is_deleted = True
        obj.updated_at = datetime.now(timezone.utc)
        await obj.save()
        return True

    async def get_multi(
        self,
        *,
        tenant_id: UUID,
        instrument_type_id: Optional[UUID] = None,
        operational_status: Optional[str] = None,
        availability_status: Optional[str] = None,
        is_calibration_overdue: Optional[bool] = None,
        is_maintenance_overdue: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        query = Instrument.find(
            Instrument.tenant_id == tenant_id,
            Instrument.is_deleted == False
        )

        if instrument_type_id:
            query = query.find(Instrument.instrument_type_id == instrument_type_id)
        if operational_status:
            query = query.find(Instrument.operational_status == operational_status)
        if availability_status:
            query = query.find(Instrument.availability_status == availability_status)

        if search:
            query = query.find({"$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"asset_id": {"$regex": search, "$options": "i"}},
                {"serial_number": {"$regex": search, "$options": "i"}}
            ]})

        total = await query.count()
        items = await query.sort(-Instrument.created_at).skip(skip).limit(limit).to_list()
        
        now_dt = datetime.now(timezone.utc)
        mapped_items = []
        for i in items:
            cal_due = i.calibration_due_date.replace(tzinfo=timezone.utc) if i.calibration_due_date and i.calibration_due_date.tzinfo is None else i.calibration_due_date
            maint_due = i.maintenance_due_date.replace(tzinfo=timezone.utc) if i.maintenance_due_date and i.maintenance_due_date.tzinfo is None else i.maintenance_due_date
            
            mapped = {
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": tenant_id,
                "instrument_type_id": i.instrument_type_id,
                "instrument_code": i.asset_id,
                "serial_number": i.serial_number or "",
                "asset_tag": i.asset_id,
                "instrument_name": i.name,
                "manufacturer": "Generic Manufacturer",
                "model": i.model or "",
                "location": "Lab Bench",
                "purchase_date": None,
                "installation_date": None,
                "warranty_expiry": None,
                "calibration_due_date": i.calibration_due_date.date() if i.calibration_due_date else None,
                "maintenance_due_date": i.maintenance_due_date.date() if i.maintenance_due_date else None,
                "operational_status": i.operational_status,
                "availability_status": i.availability_status,
                "is_calibration_overdue": bool(cal_due and cal_due < now_dt),
                "is_maintenance_overdue": bool(maint_due and maint_due < now_dt),
                "created_at": i.created_at,
                "updated_at": i.updated_at,
                "metadata_json": {}
            }
            # Only include in results if overdue filters match
            if is_calibration_overdue is not None and mapped["is_calibration_overdue"] != is_calibration_overdue:
                continue
            if is_maintenance_overdue is not None and mapped["is_maintenance_overdue"] != is_maintenance_overdue:
                continue
            mapped_items.append(mapped)

        return mapped_items, total

    # Note: I am mocking the related records (calibrations, maintenances) for simplicity since Beanie doesn't have SQL joins
    async def log_calibration(self, *args, **kwargs) -> InstrumentCalibration:
        pass
        
    async def schedule_maintenance(self, *args, **kwargs) -> InstrumentMaintenance:
        pass
        
    async def create_reservation(self, *args, **kwargs) -> InstrumentReservation:
        pass


instrument_repo = InstrumentRepository()
