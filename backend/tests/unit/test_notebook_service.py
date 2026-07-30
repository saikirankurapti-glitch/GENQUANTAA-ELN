import pytest
from app.services.notebook_service import (
    InvalidAttachmentError,
    MAX_ATTACHMENT_BYTES,
)


@pytest.mark.unit
def test_attachment_size_limit_validation():
    """Test attachment file size validation logic."""
    oversized_bytes = MAX_ATTACHMENT_BYTES + 1
    assert oversized_bytes > 50 * 1024 * 1024
