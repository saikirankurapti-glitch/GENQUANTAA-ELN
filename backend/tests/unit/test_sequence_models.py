import uuid
import pytest
from app.models.sequence import (
    Sequence,
    SequenceAnalysisResult,
    SequenceAnnotation,
    SequenceAttachment,
    SequenceVersion,
)


@pytest.mark.unit
def test_sequence_model_dna_instantiation():
    """Test Sequence model for a DNA record."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()

    seq = Sequence(
        tenant_id=tenant_id,
        organization_id=org_id,
        sequence_code="SEQ-DNA-001",
        sequence_name="pUC19 Insert",
        sequence_type="DNA",
        sequence_data="ATGCATGCATGC",
        length=12,
        gc_content=50.0,
        status="active",
        version=1,
    )
    assert seq.sequence_code == "SEQ-DNA-001"
    assert seq.sequence_type == "DNA"
    assert seq.length == 12
    assert seq.gc_content == 50.0


@pytest.mark.unit
def test_sequence_model_protein_instantiation():
    """Test Sequence model for a Protein record."""
    tenant_id = uuid.uuid4()
    org_id = uuid.uuid4()

    seq = Sequence(
        tenant_id=tenant_id,
        organization_id=org_id,
        sequence_code="SEQ-PROT-001",
        sequence_name="GFP Protein",
        sequence_type="PROTEIN",
        sequence_data="MVSKGEELFTG",
        length=11,
        gc_content=None,
        molecular_weight=26900.0,
        status="active",
        version=1,
    )
    assert seq.sequence_type == "PROTEIN"
    assert seq.gc_content is None
    assert seq.molecular_weight == 26900.0


@pytest.mark.unit
def test_sequence_version_model():
    """Test SequenceVersion model."""
    seq_id = uuid.uuid4()
    ver = SequenceVersion(
        sequence_id=seq_id,
        version_number=2,
        sequence_data="ATGCATGCATGCTTTT",
        length=16,
        gc_content=43.75,
        change_summary="Extended 3-prime end with TTTT",
    )
    assert ver.version_number == 2
    assert ver.length == 16
    assert ver.change_summary == "Extended 3-prime end with TTTT"


@pytest.mark.unit
def test_sequence_annotation_model():
    """Test SequenceAnnotation model."""
    seq_id = uuid.uuid4()
    ann = SequenceAnnotation(
        sequence_id=seq_id,
        annotation_type="ORF",
        label="Candidate ORF 1",
        start_position=1,
        end_position=300,
        strand="+",
        notes="Predicted by ORF Finder v2.1",
    )
    assert ann.annotation_type == "ORF"
    assert ann.start_position == 1
    assert ann.end_position == 300
    assert ann.strand == "+"


@pytest.mark.unit
def test_sequence_analysis_result_model():
    """Test SequenceAnalysisResult model."""
    seq_id = uuid.uuid4()
    result = SequenceAnalysisResult(
        sequence_id=seq_id,
        analysis_type="BLAST",
        tool_name="NCBI BLAST+",
        tool_version="2.14.0",
        result_summary="Top hit: E. coli K12 (E-value: 1e-120)",
        result_json={"evalue": 1e-120, "identity": 99.8},
    )
    assert result.analysis_type == "BLAST"
    assert result.tool_name == "NCBI BLAST+"
    assert result.result_json["identity"] == 99.8
