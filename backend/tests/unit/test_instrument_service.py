import pytest
from app.services.instrument_service import (
    DuplicateInstrumentAssetTag,
    DuplicateInstrumentCode,
    DuplicateInstrumentSerial,
    ExpiredCalibrationReservationError,
    InstrumentNotFound,
    InstrumentNotOperationalError,
    ReservationConflictError,
    ReservationTimeOrderError,
)


@pytest.mark.unit
def test_instrument_exception_definitions():
    """Test Instrument domain exception messages."""
    err = DuplicateInstrumentCode("Instrument code INS-MS-001 already exists.")
    assert "INS-MS-001" in str(err)

    err2 = DuplicateInstrumentSerial("Serial SN-998877 already exists.")
    assert "SN-998877" in str(err2)

    err3 = DuplicateInstrumentAssetTag("Asset tag AT-554433 already exists.")
    assert "AT-554433" in str(err3)


@pytest.mark.unit
def test_instrument_not_found_exception():
    """Test InstrumentNotFound exception message."""
    err = InstrumentNotFound("Instrument abc123 not found.")
    assert "abc123" in str(err)


@pytest.mark.unit
def test_instrument_not_operational_exception():
    """Test InstrumentNotOperationalError is raised with status context."""
    err = InstrumentNotOperationalError(
        "Cannot reserve instrument INS-MS-001 in status 'maintenance'."
    )
    assert "maintenance" in str(err)


@pytest.mark.unit
def test_reservation_conflict_exception():
    """Test ReservationConflictError messaging."""
    err = ReservationConflictError(
        "Selected reservation time slot overlaps with an existing booking."
    )
    assert "overlaps" in str(err)


@pytest.mark.unit
def test_reservation_time_order_exception():
    """Test ReservationTimeOrderError for invalid time intervals."""
    err = ReservationTimeOrderError("Reservation end time must be after start time.")
    assert "end time" in str(err)


@pytest.mark.unit
def test_expired_calibration_reservation_exception():
    """Test ExpiredCalibrationReservationError."""
    err = ExpiredCalibrationReservationError(
        "Cannot reserve instrument INS-MS-001 with overdue calibration (due: 2026-01-01)."
    )
    assert "overdue calibration" in str(err)


@pytest.mark.unit
def test_all_domain_exceptions_are_exception_subclasses():
    """Ensure all domain exceptions inherit from Exception for catchability."""
    for exc_class in [
        DuplicateInstrumentCode,
        DuplicateInstrumentSerial,
        DuplicateInstrumentAssetTag,
        InstrumentNotFound,
        InstrumentNotOperationalError,
        ReservationConflictError,
        ReservationTimeOrderError,
        ExpiredCalibrationReservationError,
    ]:
        assert issubclass(exc_class, Exception), f"{exc_class.__name__} must inherit from Exception"
