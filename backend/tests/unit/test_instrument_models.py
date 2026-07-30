import uuid
from datetime import date, datetime, timezone
import pytest
from app.models.instrument import (
    Instrument,
    InstrumentCalibration,
    InstrumentMaintenance,
    InstrumentReservation,
    InstrumentType,
    InstrumentUsage,
)


@pytest.mark.unit
def test_instrument_model_instantiation():
    """Test Instrument model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()

    instrument = Instrument(
        tenant_id=tenant_id,
        organization_id=org_id,
        instrument_code="INS-MS-001",
        serial_number="SN-998877",
        asset_tag="AT-554433",
        instrument_name="Orbitrap Mass Spectrometer",
        manufacturer="Thermo Fisher",
        model="Q Exactive HF-X",
        location="Room 402 - Bench A",
        operational_status="operational",
        availability_status="available",
    )
    assert instrument.instrument_code == "INS-MS-001"
    assert instrument.serial_number == "SN-998877"
    assert instrument.asset_tag == "AT-554433"
    assert instrument.operational_status == "operational"


@pytest.mark.unit
def test_instrument_calibration_and_maintenance_models():
    """Test InstrumentCalibration and InstrumentMaintenance models."""
    inst_id = uuid.uuid4()

    cal = InstrumentCalibration(
        instrument_id=inst_id,
        calibration_date=date(2026, 7, 1),
        calibrated_by="ISO Tech Services",
        certificate_number="CAL-2026-991",
        result="passed",
        next_due_date=date(2027, 7, 1),
    )
    assert cal.result == "passed"
    assert cal.next_due_date == date(2027, 7, 1)

    maint = InstrumentMaintenance(
        instrument_id=inst_id,
        maintenance_type="preventive",
        maintenance_date=date(2026, 6, 15),
        engineer="John Doe",
        vendor="LabCare Inc.",
        next_due_date=date(2026, 12, 15),
    )
    assert maint.maintenance_type == "preventive"
    assert maint.engineer == "John Doe"


@pytest.mark.unit
def test_instrument_reservation_and_usage_models():
    """Test InstrumentReservation and InstrumentUsage models."""
    inst_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    res = InstrumentReservation(
        instrument_id=inst_id,
        reserved_by=user_id,
        start_time=now,
        end_time=now,
        status="confirmed",
    )
    assert res.status == "confirmed"

    usage = InstrumentUsage(
        instrument_id=inst_id,
        operator_id=user_id,
        usage_start=now,
        remarks="Proteomics mass spec run.",
    )
    assert usage.remarks == "Proteomics mass spec run."
