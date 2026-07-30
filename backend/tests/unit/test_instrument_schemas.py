import uuid
from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

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


@pytest.mark.unit
def test_instrument_create_schema_valid_with_uppercase_code():
    """Test InstrumentCreate schema and uppercase validators on code, serial, asset_tag."""
    org_id = uuid.uuid4()
    obj = InstrumentCreate(
        instrument_code="ins-ms-001",
        serial_number="sn-998877",
        asset_tag="at-554433",
        instrument_name="Orbitrap Mass Spectrometer",
        manufacturer="Thermo Fisher",
        model="Q Exactive HF-X",
        organization_id=org_id,
    )
    assert obj.instrument_code == "INS-MS-001"
    assert obj.serial_number == "SN-998877"
    assert obj.asset_tag == "AT-554433"


@pytest.mark.unit
def test_instrument_create_schema_defaults():
    """Test InstrumentCreate schema default statuses."""
    org_id = uuid.uuid4()
    obj = InstrumentCreate(
        instrument_code="INS-HPLC-002",
        serial_number="SN-112233",
        asset_tag="AT-112233",
        instrument_name="HPLC System",
        manufacturer="Agilent",
        model="1260 Infinity",
        organization_id=org_id,
    )
    assert obj.operational_status == "operational"
    assert obj.availability_status == "available"
    assert obj.metadata_json == {}


@pytest.mark.unit
def test_instrument_update_schema_partial():
    """Test partial update with only supplied fields."""
    upd = InstrumentUpdate(operational_status="maintenance")
    assert upd.operational_status == "maintenance"
    assert upd.location is None
    assert upd.calibration_due_date is None


@pytest.mark.unit
def test_calibration_create_schema():
    """Test InstrumentCalibrationCreate schema."""
    cal = InstrumentCalibrationCreate(
        calibration_date=date(2026, 7, 1),
        calibrated_by="ISO Tech Services",
        certificate_number="CAL-2026-991",
        result="passed",
        next_due_date=date(2027, 7, 1),
    )
    assert cal.result == "passed"
    assert cal.calibrated_by == "ISO Tech Services"


@pytest.mark.unit
def test_maintenance_create_schema():
    """Test InstrumentMaintenanceCreate schema."""
    maint = InstrumentMaintenanceCreate(
        maintenance_type="preventive",
        maintenance_date=date(2026, 6, 15),
        engineer="John Doe",
        vendor="LabCare Inc.",
        next_due_date=date(2026, 12, 15),
    )
    assert maint.maintenance_type == "preventive"
    assert maint.next_due_date == date(2026, 12, 15)


@pytest.mark.unit
def test_reservation_create_schema():
    """Test InstrumentReservationCreate schema."""
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    end = now + timedelta(hours=2)

    res = InstrumentReservationCreate(
        start_time=now,
        end_time=end,
    )
    assert res.start_time == now
    assert res.end_time == end


@pytest.mark.unit
def test_instrument_filter_schema():
    """Test InstrumentFilter schema fields."""
    f = InstrumentFilter(operational_status="operational", search="HPLC")
    assert f.operational_status == "operational"
    assert f.search == "HPLC"


@pytest.mark.unit
def test_instrument_pagination_defaults():
    """Test InstrumentPagination default values."""
    p = InstrumentPagination()
    assert p.page == 1
    assert p.page_size == 20
    assert p.sort_by == "created_at"
    assert p.sort_order == "desc"
