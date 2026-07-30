# Functional Specification: Experiments Module

## 1. Purpose
An **Experiment** represents a structured scientific procedure executed within a research Project. It serves as the primary parent container for ELN notebook entries, protocols, samples, experimental data attachments, review sign-offs, and AI-generated summaries.

## 2. Key Features
* **Experiment Lifecycle:** Manage experiment states across `DRAFT`, `PLANNED`, `IN_PROGRESS`, `SUBMITTED`, `IN_REVIEW`, `APPROVED`, `COMPLETED`, `REJECTED`, `CANCELLED`, and `ARCHIVED`.
* **Project Container Link:** Every experiment is scoped to an active, non-archived `project_id` and isolated by `tenant_id`.
* **Collaborator Management:** Assign collaborators with explicit roles (`viewer`, `editor`, `lead`, `reviewer`).
* **Protocol & Sample Association:** Link protocols (`protocol_id`) and biological/chemical samples to experimental runs.
* **Archival & Immutability:** Archiving an experiment locks downstream modifications and preserves immutable snapshots for FDA 21 CFR Part 11 compliance.

## 3. Inputs & Outputs
* **Inputs:** `ExperimentCreate`, `ExperimentUpdate`, `ExperimentFilter`, `ExperimentCollaboratorCreate`, `ExperimentArchiveRequest`.
* **Outputs:** `ExperimentRead`, `ExperimentDetail`, `ExperimentSummary`, `ExperimentPagination`, `ExperimentListResponse`.

## 4. Dependencies
* **Tenant Module:** Workspace isolation.
* **Identity Module:** Owner (`owner_id`) and Reviewer (`reviewer_id`) user identities.
* **Projects Module:** Parent project scoping (`project_id`).
* **RBAC Module:** Permissions (`experiment.create`, `experiment.read`, `experiment.update`, `experiment.delete`, `experiment.archive`).

## 5. Workflow
```
[DRAFT / PLANNED] ---> [IN_PROGRESS] ---> [SUBMITTED / IN_REVIEW] ---> [APPROVED / COMPLETED] ---> [ARCHIVED]
```

## 6. Acceptance Criteria
1. `experiment_code` must be unique within a Project.
2. Parent project must exist, belong to the tenant, and not be archived.
3. State transitions must strictly follow valid lifecycle rules.
4. Tenant isolation must be enforced across all operations.
