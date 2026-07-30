import uuid
import pytest
from app.models.protocol import (
    Protocol,
    ProtocolApproval,
    ProtocolStep,
    ProtocolVersion,
)


@pytest.mark.unit
def test_protocol_model_instantiation():
    """Test Protocol model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()

    protocol = Protocol(
        tenant_id=tenant_id,
        organization_id=org_id,
        protocol_code="PRT-SOP-001",
        title="SDS-PAGE Electrophoresis SOP",
        description="Standard polyacrylamide gel electrophoresis procedure",
        category="biochemistry",
        status="draft",
        current_version=1,
    )
    assert protocol.protocol_code == "PRT-SOP-001"
    assert protocol.title == "SDS-PAGE Electrophoresis SOP"
    assert protocol.category == "biochemistry"
    assert protocol.status == "draft"


@pytest.mark.unit
def test_protocol_step_model():
    """Test ProtocolStep model."""
    protocol_id = uuid.uuid4()
    step = ProtocolStep(
        protocol_id=protocol_id,
        step_number=1,
        title="Prepare Resolving Gel",
        instructions="Mix 12% acrylamide solution with TEMED and APS.",
        duration_minutes=30,
        safety_notes="Wear gloves and work inside chemical fume hood.",
    )
    assert step.step_number == 1
    assert step.duration_minutes == 30


@pytest.mark.unit
def test_protocol_version_and_approval_models():
    """Test ProtocolVersion and ProtocolApproval models."""
    protocol_id = uuid.uuid4()
    approver_id = uuid.uuid4()

    version = ProtocolVersion(
        protocol_id=protocol_id,
        version_number=1,
        content_snapshot={"title": "SDS-PAGE SOP"},
        change_reason="Initial SOP release.",
    )
    assert version.version_number == 1

    approval = ProtocolApproval(
        protocol_id=protocol_id,
        approver_id=approver_id,
        status="approved",
        comments="Fully compliant with QA standards.",
    )
    assert approval.status == "approved"
