import pytest
from app.services.sequence_service import (
    DuplicateSequenceCode,
    InvalidSequenceAlphabet,
    SequenceArchivedError,
    SequenceNotFound,
    parse_fasta,
)


# ── Domain exception tests ────────────────────────────────────────────────────

@pytest.mark.unit
def test_sequence_not_found_exception():
    err = SequenceNotFound("Sequence abc-123 not found.")
    assert "abc-123" in str(err)
    assert isinstance(err, Exception)


@pytest.mark.unit
def test_duplicate_sequence_code_exception():
    err = DuplicateSequenceCode("Sequence code 'SEQ-DNA-001' already exists.")
    assert "SEQ-DNA-001" in str(err)
    assert isinstance(err, Exception)


@pytest.mark.unit
def test_invalid_sequence_alphabet_exception():
    err = InvalidSequenceAlphabet("Invalid DNA characters: U, X.")
    assert "Invalid DNA characters" in str(err)
    assert isinstance(err, Exception)


@pytest.mark.unit
def test_sequence_archived_error_exception():
    err = SequenceArchivedError("Cannot update an archived sequence.")
    assert "archived" in str(err)
    assert isinstance(err, Exception)


@pytest.mark.unit
def test_all_exceptions_are_exception_subclasses():
    for cls in [SequenceNotFound, DuplicateSequenceCode, InvalidSequenceAlphabet, SequenceArchivedError]:
        assert issubclass(cls, Exception), f"{cls.__name__} must inherit from Exception"


# ── FASTA parser tests ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_parse_fasta_single_record():
    fasta = ">SEQ001 pUC19 Insert\nATGCATGCATGC\n"
    records = parse_fasta(fasta)
    assert len(records) == 1
    assert records[0].header == "SEQ001 pUC19 Insert"
    assert records[0].sequence_data == "ATGCATGCATGC"


@pytest.mark.unit
def test_parse_fasta_multiple_records():
    fasta = (
        ">SEQ001 First sequence\n"
        "ATGCATGC\n"
        ">SEQ002 Second sequence\n"
        "GCTAGCTA\n"
        ">SEQ003 Third sequence\n"
        "TTTTAAAA\n"
    )
    records = parse_fasta(fasta)
    assert len(records) == 3
    assert records[0].sequence_data == "ATGCATGC"
    assert records[1].sequence_data == "GCTAGCTA"
    assert records[2].header == "SEQ003 Third sequence"


@pytest.mark.unit
def test_parse_fasta_multiline_sequence():
    fasta = (
        ">SEQ001 Multiline\n"
        "ATGCAT\n"
        "GCATGC\n"
        "TTAACC\n"
    )
    records = parse_fasta(fasta)
    assert len(records) == 1
    assert records[0].sequence_data == "ATGCATGCATGCTTAACC"


@pytest.mark.unit
def test_parse_fasta_empty_input():
    records = parse_fasta("")
    assert records == []


@pytest.mark.unit
def test_parse_fasta_whitespace_only():
    records = parse_fasta("   \n\n  \n")
    assert records == []


@pytest.mark.unit
def test_parse_fasta_strips_whitespace_from_sequence():
    fasta = ">SEQ001\n  ATGC ATGC  \n"
    records = parse_fasta(fasta)
    # strip() removes leading/trailing whitespace per line
    assert "ATGC" in records[0].sequence_data
