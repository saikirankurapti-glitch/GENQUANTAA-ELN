import pytest
from app.services.inventory_service import (
    DuplicateInventoryItemCode,
    ExpiredInventoryError,
    InsufficientStockError,
    InventoryItemArchivedError,
    InventoryItemNotFound,
)


@pytest.mark.unit
def test_inventory_exception_definitions():
    """Test Inventory domain exception messaging."""
    err1 = DuplicateInventoryItemCode("Item code already exists.")
    assert "Item code" in str(err1)

    err2 = InsufficientStockError("Insufficient stock balance.")
    assert "Insufficient" in str(err2)

    err3 = ExpiredInventoryError("Item is expired.")
    assert "expired" in str(err3)
