import uuid
import pytest
from app.db.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentCollaborator, ExperimentAttachment


@pytest.mark.unit
def test_experiment_model_instantiation():
    """Test Experiment ORM model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()
    project_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    exp = Experiment(
        tenant_id=tenant_id,
        organization_id=org_id,
        project_id=project_id,
        owner_id=owner_id,
        experiment_code="EXP-2026-TEST",
        title="Cell Viability Assay",
        objective="Measure cytotoxicity of compound X",
        status=ExperimentStatus.DRAFT,
        priority="HIGH",
        is_archived=False,
    )
    assert exp.experiment_code == "EXP-2026-TEST"
    assert exp.title == "Cell Viability Assay"
    assert exp.status == ExperimentStatus.DRAFT
    assert exp.priority == "HIGH"
    assert exp.is_archived is False


@pytest.mark.unit
def test_experiment_collaborator_model():
    """Test ExperimentCollaborator model attributes."""
    exp_id = uuid.uuid4()
    user_id = uuid.uuid4()

    collab = ExperimentCollaborator(
        experiment_id=exp_id,
        user_id=user_id,
        role="reviewer",
    )
    assert collab.experiment_id == exp_id
    assert collab.user_id == user_id
    assert collab.role == "reviewer"
