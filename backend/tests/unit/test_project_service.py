import pytest
from app.db.enums import ProjectStatus
from app.services.project_service import InvalidStatusTransition, project_service


@pytest.mark.unit
def test_valid_status_transitions():
    """Test valid project status state machine transitions."""
    # PLANNED -> ACTIVE
    project_service.validate_status_transition(ProjectStatus.PLANNED, ProjectStatus.ACTIVE)
    # ACTIVE -> COMPLETED
    project_service.validate_status_transition(ProjectStatus.ACTIVE, ProjectStatus.COMPLETED)
    # COMPLETED -> ARCHIVED
    project_service.validate_status_transition(ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED)


@pytest.mark.unit
def test_invalid_status_transitions():
    """Test invalid status transitions raise InvalidStatusTransition exception."""
    # PLANNED -> ARCHIVED directly (invalid)
    with pytest.raises(InvalidStatusTransition):
        project_service.validate_status_transition(ProjectStatus.PLANNED, ProjectStatus.ARCHIVED)

    # ON_HOLD -> COMPLETED directly (invalid)
    with pytest.raises(InvalidStatusTransition):
        project_service.validate_status_transition(ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED)
