import uuid
import pytest
from pydantic import ValidationError
from app.db.enums import ExperimentStatus
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate, ExperimentRead


@pytest.mark.unit
def test_experiment_create_schema_valid():
    """Test valid ExperimentCreate schema."""
    org_id = uuid.uuid4()
    project_id = uuid.uuid4()
    data = {
        "experiment_code": "exp-2026-001",
        "title": "RNA Sequencing Run #1",
        "project_id": str(project_id),
        "organization_id": str(org_id),
        "status": "draft",
        "priority": "HIGH",
    }
    obj = ExperimentCreate(**data)
    assert obj.experiment_code == "EXP-2026-001"  # UPPERCASE validator check
    assert obj.title == "RNA Sequencing Run #1"
    assert obj.status == ExperimentStatus.DRAFT


@pytest.mark.unit
def test_experiment_create_blank_code_rejection():
    """Test blank experiment_code rejection."""
    org_id = uuid.uuid4()
    project_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_code="   ",
            title="Blank Code Test",
            project_id=project_id,
            organization_id=org_id,
        )


@pytest.mark.unit
def test_experiment_update_schema():
    """Test ExperimentUpdate optional fields."""
    update = ExperimentUpdate(title="Updated Title", status=ExperimentStatus.IN_PROGRESS)
    assert update.title == "Updated Title"
    assert update.status == ExperimentStatus.IN_PROGRESS
    assert update.description is None
