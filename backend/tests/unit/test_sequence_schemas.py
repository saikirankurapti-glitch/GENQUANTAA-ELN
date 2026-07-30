import pytest
from pydantic import ValidationError

from app.schemas.sequence import (
    SequenceAnnotationCreate,
    SequenceCreate,
    SequenceFilter,
    SequencePagination,
    SequenceUpdate,
    _compute_gc_content,
    _validate_sequence_alphabet,
)
import uuid


# ── Alphabet validation helpers ───────────────────────────────────────────────

@pytest.mark.unit
def test_validate_dna_valid():
    result = _validate_sequence_alphabet("DNA", "atgcATGC")
    assert result == "ATGCATGC"


@pytest.mark.unit
def test_validate_dna_invalid_character():
    with pytest.raises(ValueError, match="Invalid DNA characters"):
        _validate_sequence_alphabet("DNA", "ATGCU")  # U not valid for DNA


@pytest.mark.unit
def test_validate_rna_valid():
    result = _validate_sequence_alphabet("RNA", "augcAUGC")
    assert result == "AUGCAUGC"


@pytest.mark.unit
def test_validate_rna_invalid_character():
    with pytest.raises(ValueError, match="Invalid RNA characters"):
        _validate_sequence_alphabet("RNA", "AUGCT")  # T not valid for RNA


@pytest.mark.unit
def test_validate_protein_valid():
    result = _validate_sequence_alphabet("PROTEIN", "MVSKGEELFTG")
    assert result == "MVSKGEELFTG"


@pytest.mark.unit
def test_validate_protein_invalid_character():
    with pytest.raises(ValueError, match="Invalid amino acid characters"):
        _validate_sequence_alphabet("PROTEIN", "MVSKBXZ")  # B, X, Z not valid


@pytest.mark.unit
def test_validate_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported sequence_type"):
        _validate_sequence_alphabet("PEPTIDE", "ACGT")


# ── GC content computation ────────────────────────────────────────────────────

@pytest.mark.unit
def test_gc_content_dna_50_percent():
    gc = _compute_gc_content("DNA", "ATGC")
    assert gc == 50.0


@pytest.mark.unit
def test_gc_content_dna_100_percent():
    gc = _compute_gc_content("DNA", "GCGCGC")
    assert gc == 100.0


@pytest.mark.unit
def test_gc_content_dna_zero_percent():
    gc = _compute_gc_content("DNA", "AAATTT")
    assert gc == 0.0


@pytest.mark.unit
def test_gc_content_rna():
    gc = _compute_gc_content("RNA", "AUGCAUGC")
    assert gc == 50.0


@pytest.mark.unit
def test_gc_content_protein_is_none():
    gc = _compute_gc_content("PROTEIN", "MVSKGEELFTG")
    assert gc is None


# ── SequenceCreate schema ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_sequence_create_dna_valid():
    obj = SequenceCreate(
        sequence_code="seq-dna-001",
        sequence_name="pUC19 Insert",
        sequence_type="DNA",
        sequence_data="atgcatgc",
        organization_id=uuid.uuid4(),
    )
    assert obj.sequence_code == "SEQ-DNA-001"
    assert obj.sequence_type == "DNA"
    assert obj.sequence_data == "ATGCATGC"


@pytest.mark.unit
def test_sequence_create_invalid_dna():
    with pytest.raises(ValidationError, match="Invalid DNA characters"):
        SequenceCreate(
            sequence_code="SEQ-DNA-002",
            sequence_name="Bad DNA",
            sequence_type="DNA",
            sequence_data="ATGCUX",   # invalid chars
            organization_id=uuid.uuid4(),
        )


@pytest.mark.unit
def test_sequence_create_rna_valid():
    obj = SequenceCreate(
        sequence_code="SEQ-RNA-001",
        sequence_name="mRNA Fragment",
        sequence_type="RNA",
        sequence_data="AUGCAUGC",
        organization_id=uuid.uuid4(),
    )
    assert obj.sequence_type == "RNA"
    assert obj.sequence_data == "AUGCAUGC"


@pytest.mark.unit
def test_sequence_create_protein_valid():
    obj = SequenceCreate(
        sequence_code="SEQ-PROT-001",
        sequence_name="GFP",
        sequence_type="PROTEIN",
        sequence_data="MVSKGEELFTG",
        organization_id=uuid.uuid4(),
    )
    assert obj.sequence_type == "PROTEIN"
    assert obj.sequence_data == "MVSKGEELFTG"


@pytest.mark.unit
def test_sequence_create_invalid_type():
    with pytest.raises(ValidationError, match="sequence_type must be DNA, RNA, or Protein"):
        SequenceCreate(
            sequence_code="SEQ-XXX-001",
            sequence_name="Unknown",
            sequence_type="PEPTIDE",
            sequence_data="ACGT",
            organization_id=uuid.uuid4(),
        )


# ── SequenceUpdate schema ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_sequence_update_partial():
    upd = SequenceUpdate(sequence_name="Updated Name")
    assert upd.sequence_name == "Updated Name"
    assert upd.sequence_data is None


# ── SequenceAnnotationCreate schema ──────────────────────────────────────────

@pytest.mark.unit
def test_annotation_create_valid():
    ann = SequenceAnnotationCreate(
        annotation_type="ORF",
        label="Candidate ORF 1",
        start_position=1,
        end_position=300,
        strand="+",
    )
    assert ann.start_position == 1
    assert ann.end_position == 300


@pytest.mark.unit
def test_annotation_create_invalid_position_order():
    with pytest.raises(ValidationError, match="end_position must be greater than start_position"):
        SequenceAnnotationCreate(
            annotation_type="CDS",
            label="Bad CDS",
            start_position=500,
            end_position=100,
        )


# ── Filter and Pagination defaults ───────────────────────────────────────────

@pytest.mark.unit
def test_sequence_filter_defaults():
    f = SequenceFilter()
    assert f.sequence_type is None
    assert f.search is None


@pytest.mark.unit
def test_sequence_pagination_defaults():
    p = SequencePagination()
    assert p.page == 1
    assert p.page_size == 20
    assert p.sort_order == "desc"
