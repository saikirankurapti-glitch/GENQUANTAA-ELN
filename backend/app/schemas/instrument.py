from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class InstrumentTypeRead(BaseModel):
    id: UUID = Field(..., description="Type identifier")
    type_name: str = Field(..., description="Classification type name (e.g. Mass Spectrometer)")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InstrumentCalibrationBase(BaseModel):
    calibration_date: date = Field(..., description="Calibration execution date")
    calibrated_by: str = Field(..., min_length=2, max_length=128, description="Engineer or agency name")
    certificate_number: Optional[str] = Field(None, description="Calibration certificate code")
    result: str = Field("passed", description="Result: passed, failed")
    remarks: Optional[str] = Field(None, description="Engineer notes")
    next_due_date: Optional[date] = Field(None, description="Next required calibration date")


class InstrumentCalibrationCreate(InstrumentCalibrationBase):
    pass


class InstrumentCalibrationRead(InstrumentCalibrationBase):
    id: UUID = Field(..., description="Calibration record identifier")
    instrument_id: UUID = Field(..., description="Instrument identifier")

    model_config = ConfigDict(from_attributes=True)


class InstrumentMaintenanceBase(BaseModel):
    maintenance_type: str = Field("preventive", description="Type: preventive, corrective, emergency")
    maintenance_date: date = Field(..., description="Maintenance execution date")
    engineer: Optional[str] = Field(None, description="Field service engineer name")
    vendor: Optional[str] = Field(None, description="Service vendor company")
    remarks: Optional[str] = Field(None, description="Service report notes")
    next_due_date: Optional[date] = Field(None, description="Next preventive maintenance date")


class InstrumentMaintenanceCreate(InstrumentMaintenanceBase):
    pass


class InstrumentMaintenanceRead(InstrumentMaintenanceBase):
    id: UUID = Field(..., description="Maintenance record identifier")
    instrument_id: UUID = Field(..., description="Instrument identifier")

    model_config = ConfigDict(from_attributes=True)


class InstrumentReservationBase(BaseModel):
    experiment_id: Optional[UUID] = Field(None, description="Associated Experiment identifier")
    start_time: datetime = Field(..., description="Booking start timestamp")
    end_time: datetime = Field(..., description="Booking end timestamp")


class InstrumentReservationCreate(InstrumentReservationBase):
    pass


class InstrumentReservationRead(InstrumentReservationBase):
    id: UUID = Field(..., description="Reservation identifier")
    instrument_id: UUID = Field(..., description="Instrument identifier")
    reserved_by: UUID = Field(..., description="Reserver user identifier")
    status: str = Field("confirmed", description="Reservation status: confirmed, cancelled, completed")

    model_config = ConfigDict(from_attributes=True)


class InstrumentUsageCreate(BaseModel):
    experiment_id: Optional[UUID] = Field(None, description="Associated Experiment identifier")
    protocol_id: Optional[UUID] = Field(None, description="Associated Protocol identifier")
    usage_start: datetime = Field(..., description="Run start timestamp")
    usage_end: Optional[datetime] = Field(None, description="Run end timestamp")
    remarks: Optional[str] = Field(None, description="Run notes or sample count")


class InstrumentUsageRead(InstrumentUsageCreate):
    id: UUID = Field(..., description="Usage log identifier")
    instrument_id: UUID = Field(..., description="Instrument identifier")
    operator_id: UUID = Field(..., description="Operator user identifier")

    model_config = ConfigDict(from_attributes=True)


class InstrumentAttachmentRead(BaseModel):
    id: UUID = Field(..., description="Attachment identifier")
    filename: str = Field(..., description="File name")
    blob_path: str = Field(..., description="Blob storage path")
    mime_type: Optional[str] = Field(None, description="MIME classification")
    file_size: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 checksum")
    uploaded_by: Optional[UUID] = Field(None, description="Uploader user identifier")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = ConfigDict(from_attributes=True)


class InstrumentBase(BaseModel):
    instrument_code: str = Field(..., min_length=2, max_length=64, description="Tenant-scoped unique code (e.g. INS-MS-001)")
    serial_number: str = Field(..., min_length=2, max_length=128, description="Manufacturer serial number")
    asset_tag: str = Field(..., min_length=2, max_length=128, description="Internal asset tag barcode")
    instrument_name: str = Field(..., min_length=2, max_length=255, description="Instrument display name")
    manufacturer: str = Field(..., min_length=2, max_length=128, description="Manufacturer company")
    model: str = Field(..., min_length=1, max_length=128, description="Model designation")
    location: Optional[str] = Field(None, description="Physical lab location (e.g. Room 402 - Bench B)")
    purchase_date: Optional[date] = Field(None, description="Purchase date")
    installation_date: Optional[date] = Field(None, description="Installation date")
    warranty_expiry: Optional[date] = Field(None, description="Warranty expiration date")
    calibration_due_date: Optional[date] = Field(None, description="Next calibration due date")
    maintenance_due_date: Optional[date] = Field(None, description="Next maintenance due date")
    operational_status: str = Field("operational", description="Status: operational, maintenance, calibration_due, out_of_service")
    availability_status: str = Field("available", description="Status: available, reserved, in_use")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")

    @field_validator("instrument_code", "serial_number", "asset_tag")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Code/serial/asset tag cannot be blank.")
        return v


class InstrumentCreate(InstrumentBase):
    organization_id: UUID = Field(..., description="Target Organization identifier")
    instrument_type_id: Optional[UUID] = Field(None, description="Instrument classification type identifier")


class InstrumentUpdate(BaseModel):
    instrument_name: Optional[str] = Field(None, min_length=2, max_length=255)
    location: Optional[str] = None
    calibration_due_date: Optional[date] = None
    maintenance_due_date: Optional[date] = None
    operational_status: Optional[str] = None
    availability_status: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class InstrumentRead(InstrumentBase):
    id: UUID = Field(..., description="Instrument unique identifier")
    tenant_id: UUID = Field(..., description="Tenant workspace identifier")
    organization_id: UUID = Field(..., description="Organization identifier")
    instrument_type_id: Optional[UUID] = Field(None, description="Type classification identifier")
    is_calibration_overdue: bool = Field(False, description="Computed calibration overdue flag")
    is_maintenance_overdue: bool = Field(False, description="Computed maintenance overdue flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class InstrumentDetail(InstrumentRead):
    instrument_type: Optional[InstrumentTypeRead] = Field(None, description="Type detail")
    calibrations: List[InstrumentCalibrationRead] = Field(default_factory=list, description="Calibration history")
    maintenances: List[InstrumentMaintenanceRead] = Field(default_factory=list, description="Maintenance history")
    reservations: List[InstrumentReservationRead] = Field(default_factory=list, description="Upcoming reservations")
    usage_history: List[InstrumentUsageRead] = Field(default_factory=list, description="Usage run history")
    attachments: List[InstrumentAttachmentRead] = Field(default_factory=list, description="Attached documentation")


class InstrumentSummary(BaseModel):
    id: UUID
    instrument_code: str
    instrument_name: str
    operational_status: str
    availability_status: str

    model_config = ConfigDict(from_attributes=True)


class InstrumentFilter(BaseModel):
    instrument_type_id: Optional[UUID] = None
    operational_status: Optional[str] = None
    availability_status: Optional[str] = None
    is_calibration_overdue: Optional[bool] = Field(None, description="Filter items with overdue calibration")
    search: Optional[str] = Field(None, description="Search keyword matching code, serial, asset tag, or name")


class InstrumentPagination(BaseModel):
    page: int = Field(1, ge=1, description="Page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: str = Field("desc", description="Sort direction: asc or desc")


class InstrumentListResponse(BaseModel):
    items: List[InstrumentRead] = Field(default_factory=list, description="Page of instrument records")
    total: int = Field(0, description="Total matching instruments count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Page size")
    total_pages: int = Field(1, description="Total pages count")
