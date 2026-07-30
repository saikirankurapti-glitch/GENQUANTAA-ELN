# Functional Specification: Sample Registry Module

## 1. Purpose
The **Sample Registry Module** manages biological, chemical, analytical, and physical laboratory samples utilized during scientific experiments. It provides sample barcode tracking, quantity/concentration logging, storage location mapping, chain-of-custody audit logs, and parent-child sample lineage tracking.

## 2. Key Features
* **Sample Lifecycle:** Register, update, search, archive, restore, and soft-delete lab samples across states (`AVAILABLE`, `CONSUMED`, `DESTROYED`, `TRANSFERRED`, `EXPIRED`, `ARCHIVED`).
* **Experiment Scoping:** Every Sample belongs to an active, non-archived `experiment_id` and is isolated by `tenant_id`.
* **Barcode & Code Uniqueness:** `sample_code` is unique within an Experiment; `barcode` is globally unique within a tenant.
* **Chain of Custody:** Track every sample transfer, check-in, check-out, consumption, or status change with `SampleChainOfCustody` records.
* **Storage Location & Temperature:** Associate samples with storage units (`SampleStorageLocation`) and validate required storage temperatures.

## 3. Inputs & Outputs
* **Inputs:** `SampleCreate`, `SampleUpdate`, `SampleFilter`, `SampleAttachmentCreate`.
* **Outputs:** `SampleRead`, `SampleDetail`, `SampleSummary`, `ChainOfCustodyRead`, `StorageLocationRead`, `SampleListResponse`.

## 4. Dependencies
* **Tenant Module:** Workspace isolation.
* **Identity Module:** User creator, handler, and custodian identities.
* **Experiments Module:** Parent experiment scoping (`experiment_id`).
* **RBAC Module:** Permissions (`sample.create`, `sample.read`, `sample.update`, `sample.delete`).

## 5. Workflow
```
[REGISTER SAMPLE] ---> [CHECK OUT / TRANSFER] ---> [CHAIN OF CUSTODY LOGGED] ---> [CONSUMED / EXPIRED]
```

## 6. Acceptance Criteria
1. `sample_code` must be unique per Experiment; `barcode` must be unique per Tenant.
2. Parent experiment must exist and must not be archived.
3. Quantity and concentration must be positive non-negative values.
4. Chain of custody audit records must be generated on custodian transfers.
