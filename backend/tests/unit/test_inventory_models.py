import uuid
import pytest
from app.models.inventory import (
    InventoryBatch,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventorySupplier,
    InventoryTransaction,
)


@pytest.mark.unit
def test_inventory_item_model_instantiation():
    """Test InventoryItem model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()

    item = InventoryItem(
        tenant_id=tenant_id,
        organization_id=org_id,
        item_code="INV-RGT-001",
        item_name="Sodium Chloride AR Grade",
        unit="kg",
        minimum_stock=5.0,
        current_stock=25.0,
        reorder_level=10.0,
        status="available",
    )
    assert item.item_code == "INV-RGT-001"
    assert item.item_name == "Sodium Chloride AR Grade"
    assert item.current_stock == 25.0
    assert item.reorder_level == 10.0


@pytest.mark.unit
def test_inventory_category_and_location_models():
    """Test InventoryCategory and InventoryLocation models."""
    cat = InventoryCategory(
        name="Chemical Reagents",
        code="CHEM",
        description="Analytical and AR grade chemical salts",
    )
    assert cat.code == "CHEM"

    loc = InventoryLocation(
        name="Cabinet-02 Shelf-A",
        building="Chem Core Building",
        room="105",
        cabinet_shelf="Cab-02-A",
    )
    assert loc.name == "Cabinet-02 Shelf-A"
    assert loc.room == "105"


@pytest.mark.unit
def test_inventory_batch_and_transaction_models():
    """Test InventoryBatch and InventoryTransaction models."""
    item_id = uuid.uuid4()
    user_id = uuid.uuid4()

    batch = InventoryBatch(
        inventory_item_id=item_id,
        lot_number="LOT-202607-001",
        batch_quantity=100.0,
        status="active",
    )
    assert batch.lot_number == "LOT-202607-001"
    assert batch.batch_quantity == 100.0

    tx = InventoryTransaction(
        inventory_item_id=item_id,
        transaction_type="receive",
        quantity=100.0,
        performed_by=user_id,
        remarks="Stock check-in from PO #9948.",
    )
    assert tx.transaction_type == "receive"
    assert tx.quantity == 100.0
