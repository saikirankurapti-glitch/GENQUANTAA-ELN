import uuid
import pytest
from pydantic import ValidationError
from app.schemas.notebook import (
    NotebookCommentCreate,
    NotebookEntryCreate,
    NotebookEntryUpdate,
    NotebookTagCreate,
)


@pytest.mark.unit
def test_notebook_entry_create_schema_valid():
    """Test valid NotebookEntryCreate schema."""
    org_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    data = {
        "entry_number": "nbe-2026-001",
        "title": "Protein Crystallization Run",
        "experiment_id": str(exp_id),
        "organization_id": str(org_id),
        "content": {"buffer": "Tris-HCl pH 7.5"},
    }
    obj = NotebookEntryCreate(**data)
    assert obj.entry_number == "NBE-2026-001"  # UPPERCASE validator check
    assert obj.title == "Protein Crystallization Run"


@pytest.mark.unit
def test_notebook_entry_blank_number_rejection():
    """Test blank entry_number rejection."""
    org_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        NotebookEntryCreate(
            entry_number="   ",
            title="Blank Number Test",
            experiment_id=exp_id,
            organization_id=org_id,
        )


@pytest.mark.unit
def test_notebook_comment_and_tag_schemas():
    """Test comment and tag schema validations."""
    comment = NotebookCommentCreate(comment="Looks solid.")
    assert comment.comment == "Looks solid."

    tag = NotebookTagCreate(tag_name="GxP", color="#EF4444")
    assert tag.tag_name == "GxP"
    assert tag.color == "#EF4444"
