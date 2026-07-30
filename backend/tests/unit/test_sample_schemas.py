import uuid
import pytest
from pydantic import ValidationError
from app.schemas.sample import (
    SampleCreate,
    SampleUpdate,
)


@pytest.mark.unit
def test_sample_create_schema_valid():
    """Test valid SampleCreate schema and uppercase validators."""
    org_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    data = {
        "sample_code": "smp-001",
        "barcode": "bc-100234",
        "sample_name": "HEK293 Cell Pellet",
        "experiment_id": str(exp_id),
        "organization_id": str(org_id),
        "quantity": 10.5,
        "unit": "vials",
    }
    obj = SampleCreate(**data)
    assert obj.sample_code == "SMP-001"  # UPPERCASE validator check
    assert obj.barcode == "BC-100234"      # UPPERCASE validator check
    assert obj.quantity == 10.5


@pytest.mark.unit
def test_sample_negative_quantity_rejection():
    """Test negative quantity validation rejection."""
    org_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_code="SMP-002",
            barcode="BC-100235",
            sample_name="Invalid Quantity Test",
            experiment_id=exp_id,
            organization_id=org_id,
            quantity=-5.0,  # Negative quantity should fail ge=0.0 constraint
        )


@pytest.mark.unit
def test_sample_update_schema():
    """Test SampleUpdate schema partial update attributes."""
    obj = SampleUpdate(quantity=15.0, status="consumed")
    assert obj.quantity == 15.0
    assert obj.status == "consumed"
