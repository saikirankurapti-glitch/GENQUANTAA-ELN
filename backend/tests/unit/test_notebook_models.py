import uuid
import pytest
from app.models.notebook import (
    NotebookAttachment,
    NotebookComment,
    NotebookEntry,
    NotebookEntryVersion,
    NotebookTag,
)


@pytest.mark.unit
def test_notebook_entry_model_instantiation():
    """Test NotebookEntry model instantiation and attributes."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()
    exp_id = uuid.uuid4()

    entry = NotebookEntry(
        tenant_id=tenant_id,
        organization_id=org_id,
        experiment_id=exp_id,
        entry_number="NBE-001",
        title="Initial Mass Spec Observations",
        content={"notes": "Observed peak at 450 m/z"},
        entry_type="observation",
        current_version=1,
        is_locked=False,
    )
    assert entry.entry_number == "NBE-001"
    assert entry.title == "Initial Mass Spec Observations"
    assert entry.current_version == 1
    assert entry.is_locked is False


@pytest.mark.unit
def test_notebook_version_model():
    """Test NotebookEntryVersion immutable snapshot attributes."""
    entry_id = uuid.uuid4()
    version = NotebookEntryVersion(
        notebook_entry_id=entry_id,
        version_number=2,
        content_snapshot={"notes": "Corrected peak to 452 m/z"},
        change_reason="Calibration adjustment",
    )
    assert version.notebook_entry_id == entry_id
    assert version.version_number == 2
    assert version.change_reason == "Calibration adjustment"


@pytest.mark.unit
def test_notebook_comment_and_tag_models():
    """Test NotebookComment and NotebookTag models."""
    entry_id = uuid.uuid4()
    author_id = uuid.uuid4()

    comment = NotebookComment(
        notebook_entry_id=entry_id,
        author_id=author_id,
        comment="Peer review verified.",
    )
    assert comment.comment == "Peer review verified."

    tag = NotebookTag(
        notebook_entry_id=entry_id,
        tag_name="HPLC",
        color="#10B981",
    )
    assert tag.tag_name == "HPLC"
    assert tag.color == "#10B981"
