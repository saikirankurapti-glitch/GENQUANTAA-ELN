import uuid
import pytest
from pydantic import ValidationError
from app.schemas.inventory import (
    InventoryIssueRequest,
    InventoryItemCreate,
    InventoryReceiveRequest,
)


@pytest.mark.unit
def test_inventory_item_create_schema_valid():
    """Test valid InventoryItemCreate schema and uppercase code validator."""
    org_id = uuid.uuid4()
    data = {
        "item_code": "inv-media-005",
        "item_name": "DMEM High Glucose Medium",
        "organization_id": str(org_id),
        "unit": "bottles",
        "initial_stock": 50.0,
        "minimum_stock": 10.0,
        "reorder_level": 15.0,
    }
    obj = InventoryItemCreate(**data)
    assert obj.item_code == "INV-MEDIA-005"  # UPPERCASE validator check
    assert obj.initial_stock == 50.0


@pytest.mark.unit
def test_inventory_stock_request_schemas():
    """Test receive and issue stock request validations."""
    recv = InventoryReceiveRequest(quantity=20.0, remarks="PO-1002 receiving")
    assert recv.quantity == 20.0

    issue = InventoryIssueRequest(quantity=5.0, remarks="Experiment EXP-001 buffer prep")
    assert issue.quantity == 5.0


@pytest.mark.unit
def test_inventory_negative_stock_rejection():
    """Test negative quantity rejection in stock requests."""
    with pytest.raises(ValidationError):
        InventoryIssueRequest(quantity=-5.0)
