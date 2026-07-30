import uuid
import pytest
from pydantic import ValidationError
from app.db.enums import ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead


@pytest.mark.unit
def test_project_create_schema_valid():
    """Test valid ProjectCreate schema."""
    org_id = uuid.uuid4()
    data = {
        "project_code": "prj-2026-001",
        "name": "CRISPR Gene Editing",
        "organization_id": str(org_id),
        "status": "planned",
        "priority": "HIGH",
    }
    obj = ProjectCreate(**data)
    assert obj.project_code == "PRJ-2026-001"  # UPPERCASE validator check
    assert obj.name == "CRISPR Gene Editing"
    assert obj.status == ProjectStatus.PLANNED


@pytest.mark.unit
def test_project_create_blank_code_rejection():
    """Test blank project_code rejection."""
    org_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_code="   ",
            name="Blank Code Test",
            organization_id=org_id,
        )


@pytest.mark.unit
def test_project_update_schema():
    """Test ProjectUpdate optional fields."""
    update = ProjectUpdate(name="Renamed Project", status=ProjectStatus.ACTIVE)
    assert update.name == "Renamed Project"
    assert update.status == ProjectStatus.ACTIVE
    assert update.description is None
