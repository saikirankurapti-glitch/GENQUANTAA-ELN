# Functional Specification: ELN Notebook Module

## 1. Purpose
The **ELN Notebook Module** provides an immutable, version-controlled scientific ledger for recording experimental data, rich text notes, observations, attachments, comments, tags, and AI-generated summaries. Every Notebook Entry belongs to exactly one Experiment container.

## 2. Key Features
* **Immutable Versioning:** Editing a notebook entry NEVER overwrites historical content. Every update creates an incremental `NotebookEntryVersion` snapshot (`version_number=1, 2, 3...`) with change reasons.
* **Experiment Containment:** Every entry is linked to an active, non-archived `experiment_id` and strictly scoped by `tenant_id`.
* **Collaborative Discussion & Tagging:** Add nested comments (`NotebookComment`) and color-coded tags (`NotebookTag`).
* **Attachment Auditing:** Upload attached raw files (`NotebookAttachment`) with file size, checksum, and MIME verification.
* **AI Summary Integration:** Automatic placeholder and summary status tracking (`PENDING`, `GENERATING`, `COMPLETED`, `FAILED`).

## 3. Inputs & Outputs
* **Inputs:** `NotebookEntryCreate`, `NotebookEntryUpdate`, `NotebookCommentCreate`, `NotebookTagCreate`, `NotebookAttachmentCreate`.
* **Outputs:** `NotebookEntryRead`, `NotebookEntryDetail`, `NotebookEntrySummary`, `NotebookEntryVersionRead`, `NotebookListResponse`.

## 4. Dependencies
* **Tenant Module:** Workspace isolation.
* **Identity Module:** User authorship (`created_by`, `author_id`).
* **Experiments Module:** Parent experiment scoping (`experiment_id`).
* **RBAC Module:** Permissions (`notebook.create`, `notebook.read`, `notebook.update`, `notebook.delete`).

## 5. Versioning Rules
1. Initial creation creates `NotebookEntry` and `NotebookEntryVersion` version `1`.
2. Any subsequent edit increments `current_version` and stores an immutable snapshot in `NotebookEntryVersion`.
3. Historical versions are read-only and preserved for FDA 21 CFR Part 11 ALCOA+ compliance.

## 6. Acceptance Criteria
1. `entry_number` must be unique per Experiment.
2. Parent experiment must exist and must not be archived.
3. Editing an entry must create a new immutable `NotebookEntryVersion`.
4. Tenant isolation must be strictly enforced.
