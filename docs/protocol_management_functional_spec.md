# Functional Specification: Protocol Management Module

## 1. Purpose
The **Protocol Management Module** stores and manages standardized laboratory procedures, experimental workflows, and assay protocols that can be linked to scientific experiments. It provides immutable version control, multi-step sequence management, formal review/approval workflows, attachment handling, and reuse across multiple experiments.

## 2. Key Features
* **Standard Operating Procedures (SOPs):** Maintain reusable laboratory protocols classified by category (`molecular_biology`, `biochemistry`, `analytical`, `cell_culture`).
* **Immutable Versioning:** Editing an approved protocol increments `current_version` and stores a read-only snapshot in `ProtocolVersion`.
* **Step Ordering:** Manage sequential protocol execution steps (`ProtocolStep`) with step number, action instructions, required duration, and safety notes.
* **Approval Workflows:** Track review/approval events (`ProtocolApproval`) approving or rejecting protocols.
* **Experiment Linking:** Only approved protocols can be linked to active scientific experiments.

## 3. Inputs & Outputs
* **Inputs:** `ProtocolCreate`, `ProtocolUpdate`, `ProtocolStepCreate`, `ProtocolApprovalCreate`, `ProtocolFilter`.
* **Outputs:** `ProtocolRead`, `ProtocolDetail`, `ProtocolSummary`, `ProtocolVersionRead`, `ProtocolStepRead`, `ProtocolApprovalRead`, `ProtocolListResponse`.

## 4. Dependencies
* **Tenant Module:** Workspace isolation.
* **Identity Module:** Owner, reviewer, and approver user identities.
* **RBAC Module:** Permissions (`protocol.create`, `protocol.read`, `protocol.update`, `protocol.approve`).

## 5. Workflow
```
[DRAFT PROTOCOL] ---> [ADD STEPS / ATTACHMENTS] ---> [SUBMIT FOR REVIEW] ---> [APPROVED] ---> [LINK TO EXPERIMENTS]
```

## 6. Acceptance Criteria
1. `protocol_code` must be globally unique within a tenant.
2. Editing an approved protocol must create a new immutable version snapshot.
3. Steps must be strictly ordered by `step_number`.
4. Only `APPROVED` status protocols can be linked to experiments.
