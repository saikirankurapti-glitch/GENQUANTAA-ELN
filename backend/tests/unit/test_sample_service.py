import pytest
from app.services.sample_service import (
    DuplicateSampleBarcode,
    DuplicateSampleCode,
    InvalidSampleQuantityError,
    SampleArchivedError,
    SampleNotFound,
)


@pytest.mark.unit
def test_sample_exception_hierarchy():
    """Test Sample domain exception definitions."""
    err1 = DuplicateSampleCode("Sample code already exists.")
    assert "Sample code" in str(err1)

    err2 = DuplicateSampleBarcode("Barcode already exists.")
    assert "Barcode" in str(err2)

    err3 = InvalidSampleQuantityError("Quantity cannot be negative.")
    assert "negative" in str(err3)
