# Functional Specification: DNA/RNA/Protein Sequence Management Module

## 1. Purpose
The **Sequence Management Module** manages DNA, RNA, and Protein sequences associated with laboratory samples and experiments. It supports FASTA upload, manual entry, biological validation, GC content computation, molecular weight storage, versioning, annotations, and analysis result tracking.

## 2. Supported Sequence Types
| Type | Alphabet | GC Content | Notes |
|---|---|---|---|
| DNA | A, C, G, T | Yes | Double-stranded |
| RNA | A, C, G, U | Yes | Single-stranded |
| Protein | 20 standard amino acid codes | No | Molecular weight tracked |

## 3. Key Features
- **FASTA Upload:** Parse single or multi-record FASTA files and bulk-register sequences.
- **Manual Entry:** Submit raw sequence strings with metadata.
- **Biological Validation:** Reject sequences containing invalid nucleotide or amino acid characters.
- **Auto-Computation:** Calculate sequence length, GC content (DNA/RNA), and store molecular weight.
- **Versioning:** Every update to sequence data creates a new `SequenceVersion` record.
- **Annotations:** Tag specific residue positions with functional annotations.
- **Attachments:** Attach FASTA files, alignment files, chromatograms, and reports.
- **Analysis Results:** Store external analysis outputs (BLAST, ORF prediction, secondary structure).
- **Links:** Associate sequences with existing `Sample` and `Experiment` records.

## 4. Inputs & Outputs
- **Inputs:** `SequenceCreate`, `SequenceUpdate`, FASTA file upload, `SequenceAnnotationCreate`, `SequenceFilter`.
- **Outputs:** `SequenceRead`, `SequenceDetail`, `SequenceSummary`, `SequenceVersionRead`, `SequenceAnnotationRead`, `SequenceAttachmentRead`, `SequenceAnalysisResultRead`, `SequenceListResponse`.

## 5. Business Rules
1. `sequence_code` must be globally unique per tenant.
2. DNA sequences must contain only characters `A`, `C`, `G`, `T` (case-insensitive).
3. RNA sequences must contain only characters `A`, `C`, `G`, `U` (case-insensitive).
4. Protein sequences must contain only valid IUPAC single-letter amino acid codes.
5. `length` is automatically computed from `sequence_data`.
6. `gc_content` is automatically computed for DNA/RNA as `(G+C) / length × 100`.
7. Sequence data updates always increment `version` and archive the prior version in `SequenceVersion`.
8. Archived sequences cannot be updated.

## 6. Workflow
```
[UPLOAD FASTA / MANUAL ENTRY] → [VALIDATE ALPHABET] → [COMPUTE LENGTH / GC] → [REGISTER SEQUENCE]
       → [ANNOTATE RESIDUES] → [ATTACH FILES] → [SAVE ANALYSIS RESULTS] → [VERSION ON UPDATE]
```

## 7. Dependencies
- `Sample` (foreign key, optional)
- `Experiment` (foreign key, optional)
- `Organization`
- `Tenant`
- `User` (created_by, updated_by)

## 8. Acceptance Criteria
1. Invalid nucleotide/amino acid characters must be rejected with a `422` validation error.
2. GC content and length must be auto-computed on creation and update.
3. Every sequence data change must produce a new version record.
4. FASTA upload must parse and register all records from a valid FASTA file.
5. Sequence code uniqueness must be enforced per tenant.
