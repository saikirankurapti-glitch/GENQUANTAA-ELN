from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document
from uuid import UUID, uuid4

class InstrumentType(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "instrument_types"

class Instrument(Document):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    instrument_type_id: Optional[UUID] = None
    name: str
    asset_id: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    operational_status: str = "operational"
    availability_status: str = "available"
    is_operational: bool = True
    calibration_due_date: Optional[datetime] = None
    maintenance_due_date: Optional[datetime] = None
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "instruments"

class InstrumentCalibration(Document):
    id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    calibrated_at: datetime
    status: str = "passed"
    notes: Optional[str] = None

    class Settings:
        name = "instrument_calibrations"

class InstrumentMaintenance(Document):
    id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    performed_at: datetime
    notes: Optional[str] = None

    class Settings:
        name = "instrument_maintenances"

class InstrumentReservation(Document):
    id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "instrument_reservations"

class InstrumentUsage(Document):
    id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None

    class Settings:
        name = "instrument_usages"

class InstrumentAttachment(Document):
    id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    file_name: str
    file_path: str

    class Settings:
        name = "instrument_attachments"
