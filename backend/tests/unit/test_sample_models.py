import uuid
import pytest
from app.models.sample import (
    Sample,
    SampleChainOfCustody,
    SampleStorageLocation,
    SampleType,
)


@pytest.mark.unit
def test_sample_model_instantiation():
    """Test Sample model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()
    exp_id = uuid.uuid4()

    sample = Sample(
        tenant_id=tenant_id,
        organization_id=org_id,
        experiment_id=exp_id,
        sample_code="SMP-2026-001",
        barcode="BC-998877",
        sample_name="Purified Monoclonal Antibody Target A",
        quantity=50.0,
        unit="mg",
        concentration="5.0 mg/mL",
        storage_temperature="-80C",
        status="available",
    )
    assert sample.sample_code == "SMP-2026-001"
    assert sample.barcode == "BC-998877"
    assert sample.quantity == 50.0
    assert sample.status == "available"


@pytest.mark.unit
def test_sample_type_and_location_models():
    """Test SampleType and SampleStorageLocation models."""
    sample_type = SampleType(
        name="Protein / Antibody",
        code="PROT_MAB",
        description="Recombinant antibody specimen",
    )
    assert sample_type.code == "PROT_MAB"

    location = SampleStorageLocation(
        name="Freezer-04 Rack-B Box-12",
        building="Main BioLab",
        room="302",
        freezer_unit="ULT-80-04",
    )
    assert location.name == "Freezer-04 Rack-B Box-12"
    assert location.room == "302"


@pytest.mark.unit
def test_sample_chain_of_custody_model():
    """Test SampleChainOfCustody model."""
    sample_id = uuid.uuid4()
    custodian_id = uuid.uuid4()

    coc = SampleChainOfCustody(
        sample_id=sample_id,
        action="transferred",
        custodian_id=custodian_id,
        remarks="Transferred to Analytics Core for HPLC assay.",
    )
    assert coc.action == "transferred"
    assert coc.remarks == "Transferred to Analytics Core for HPLC assay."
