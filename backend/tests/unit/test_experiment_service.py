import pytest
from app.db.enums import ExperimentStatus
from app.services.experiment_service import InvalidExperimentStatusTransition, experiment_service


@pytest.mark.unit
def test_valid_experiment_status_transitions():
    """Test valid experiment status state machine transitions."""
    # DRAFT -> PLANNED
    experiment_service.validate_status_transition(ExperimentStatus.DRAFT, ExperimentStatus.PLANNED)
    # PLANNED -> IN_PROGRESS
    experiment_service.validate_status_transition(ExperimentStatus.PLANNED, ExperimentStatus.IN_PROGRESS)
    # IN_PROGRESS -> SUBMITTED
    experiment_service.validate_status_transition(ExperimentStatus.IN_PROGRESS, ExperimentStatus.SUBMITTED)
    # SUBMITTED -> APPROVED
    experiment_service.validate_status_transition(ExperimentStatus.SUBMITTED, ExperimentStatus.APPROVED)
    # APPROVED -> ARCHIVED
    experiment_service.validate_status_transition(ExperimentStatus.APPROVED, ExperimentStatus.ARCHIVED)


@pytest.mark.unit
def test_invalid_experiment_status_transitions():
    """Test invalid status transitions raise InvalidExperimentStatusTransition exception."""
    # DRAFT -> ARCHIVED directly (invalid)
    with pytest.raises(InvalidExperimentStatusTransition):
        experiment_service.validate_status_transition(ExperimentStatus.DRAFT, ExperimentStatus.ARCHIVED)

    # REJECTED -> ARCHIVED directly (invalid)
    with pytest.raises(InvalidExperimentStatusTransition):
        experiment_service.validate_status_transition(ExperimentStatus.REJECTED, ExperimentStatus.ARCHIVED)
