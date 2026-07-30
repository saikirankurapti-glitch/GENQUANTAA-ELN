import pytest
from app.services.protocol_service import (
    DuplicateProtocolCode,
    InvalidProtocolStepOrder,
    ProtocolApprovedImmutableError,
    ProtocolNotFound,
    UnapprovedProtocolLinkError,
)


@pytest.mark.unit
def test_protocol_exception_definitions():
    """Test Protocol domain exception messaging."""
    err1 = DuplicateProtocolCode("Protocol code already exists.")
    assert "Protocol code" in str(err1)

    err2 = InvalidProtocolStepOrder("Step number must be positive.")
    assert "positive" in str(err2)

    err3 = UnapprovedProtocolLinkError("Only approved protocols can be linked.")
    assert "approved" in str(err3)
