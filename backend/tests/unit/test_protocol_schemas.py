import uuid
import pytest
from pydantic import ValidationError
from app.schemas.protocol import (
    ProtocolApprovalCreate,
    ProtocolCreate,
    ProtocolStepCreate,
    ProtocolUpdate,
)


@pytest.mark.unit
def test_protocol_create_schema_valid():
    """Test valid ProtocolCreate schema and uppercase code validator."""
    org_id = uuid.uuid4()
    data = {
        "protocol_code": "sop-pcr-002",
        "title": "Taq Polymerase PCR Amplification",
        "organization_id": str(org_id),
        "category": "molecular_biology",
        "steps": [
            {
                "step_number": 1,
                "title": "Master Mix Preparation",
                "instructions": "Combine dNTPs, primers, buffer, and Taq polymerase on ice.",
                "duration_minutes": 15,
            }
        ],
    }
    obj = ProtocolCreate(**data)
    assert obj.protocol_code == "SOP-PCR-002"  # UPPERCASE validator check
    assert len(obj.steps) == 1
    assert obj.steps[0].step_number == 1


@pytest.mark.unit
def test_protocol_invalid_step_number_rejection():
    """Test non-positive step number rejection."""
    with pytest.raises(ValidationError):
        ProtocolStepCreate(
            step_number=0,  # Fails ge=1 constraint
            title="Invalid Step Index",
            instructions="This should fail.",
        )


@pytest.mark.unit
def test_protocol_approval_schema():
    """Test ProtocolApprovalCreate schema."""
    obj = ProtocolApprovalCreate(status="approved", comments="Validated by QA Lead.")
    assert obj.status == "approved"
    assert obj.comments == "Validated by QA Lead."
