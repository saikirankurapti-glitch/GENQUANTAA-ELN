import uuid
import pytest
from app.db.enums import ProjectStatus
from app.models.project import Project, ProjectCollaborator, ProjectAttachment


@pytest.mark.unit
def test_project_model_instantiation():
    """Test Project ORM model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    project = Project(
        tenant_id=tenant_id,
        organization_id=org_id,
        owner_id=owner_id,
        project_code="PRJ-2026-TEST",
        name="Oncology Biomarker Study",
        description="Targeted therapy research",
        status=ProjectStatus.ACTIVE,
        priority="HIGH",
        visibility="ORGANIZATION",
        is_archived=False,
    )
    assert project.project_code == "PRJ-2026-TEST"
    assert project.name == "Oncology Biomarker Study"
    assert project.status == ProjectStatus.ACTIVE
    assert project.priority == "HIGH"
    assert project.is_archived is False


@pytest.mark.unit
def test_project_collaborator_model():
    """Test ProjectCollaborator model attributes."""
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()

    collab = ProjectCollaborator(
        project_id=project_id,
        user_id=user_id,
        role="editor",
    )
    assert collab.project_id == project_id
    assert collab.user_id == user_id
    assert collab.role == "editor"
