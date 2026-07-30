# Physical Database Design (PDD) & Master Architectural Blueprint

This document represents the finalized Physical Database Design (PDD) for the enterprise Electronic Laboratory Notebook (ELN) platform. It compiles the architecture reviews, validates normalized schemas, and acts as the single source of truth for all future development.

---

## 1. Database Inventory

The platform operates on a logical database strategy within a single high-availability PostgreSQL cluster.

| Logical Database | Purpose | Business Capabilities | Performance Class |
| :--- | :--- | :--- | :--- |
| **`eln_platform_db`** | Root system control and tenant registration. | Tenant provisioning, billing subscription, system health logs, and domain routing. | OLTP - Low read/write frequency |
| **`eln_tenant_db`** | Core operational workspace (Logical schemas per tenant). | Users, RBAC, Research Projects, Sample Registries, workflows, and compliance trails. | OLTP - High read/write frequency |
| **`eln_vector_db`** | AI semantic storage. | High-dimensional vectors for semantic search, prompt caching, and context index. | Hybrid - High-read, low-write |

---

## 2. Schema Inventory

Logical database domains are isolated into schemas within each tenant’s database space (`tenant_{tenant_uuid}`):

*   **`identity`**: User profiles, credentials hash, security configurations, and API keys.
*   **`organization`**: Structuring departments, corporate sites, teams, and lab registries.
*   **`research`**: Core scientific records including projects, experimental designs, and protocols.
*   **`inventory`**: Sample metadata records, storage configurations, barcodes, and chains of custody.
*   **`workflow`**: Dynamic approval engines, validation lines, and routing histories.
*   **`compliance`**: Cryptographic lock hashes, signature manifestation, and digital profiles.
*   **`audit`**: Immutable database-trigger audit logs.
*   **`collaboration`**: In-app comments, attachments, activity streams, and alerts.
*   **`ai`**: Model prompt templates and high-dimensional search indices.

---

## 3. Module Inventory

Each business module is matched directly to its database and schema scope.

```
├── Identity Module           --> eln_tenant_db.identity
├── Organization Module       --> eln_tenant_db.organization
├── Research LIMS Module      --> eln_tenant_db.research
├── Sample Registry Module    --> eln_tenant_db.inventory
├── Workflow Engine Module    --> eln_tenant_db.workflow
├── Compliance Module         --> eln_tenant_db.compliance
├── Collaboration Module      --> eln_tenant_db.collaboration
├── AI Integration Module     --> eln_vector_db.ai
```

---

## 4. Master Tables

Master tables store slow-changing structural configurations that define the LIMS setup.

1.  `tenants` (`platform` schema)
2.  `users` (`identity` schema)
3.  `roles` / `permissions` (`identity` schema)
4.  `organizations` / `departments` / `teams` (`organization` schema)
5.  `projects` / `studies` (`research` schema)
6.  `sample_types` (`inventory` schema)
7.  `locations` / `containers` (`inventory` schema)
8.  `instrument_types` (`inventory` schema)

---

## 5. Transaction Tables

Transaction tables capture high-frequency operations, requiring index optimization, partitioning, and cold-storage archiving rules.

1.  `experiments`: Science draft changes.
2.  `experiment_versions`: Locked immutable procedures.
3.  `transfers`: Physical move logs.
4.  `login_histories` / `user_sessions`: Security access logs.
5.  `workflow_executions`: Active document approval routes.
6.  `instrument_runs`: Live raw data telemetry captures.
7.  `comments` / `attachments`: Scientist discussions.

---

## 6. Lookup Tables

Lookup tables define static categorical domains to ensure referential integrity.

1.  `user_status_lookup`: Maps status domains (`active`, `inactive`, `suspended`).
2.  `project_status_lookup`: Maps project progress states (`planned`, `active`, `completed`).
3.  `experiment_status_lookup`: Maps review progress (`draft`, `in_review`, `approved`, `rejected`).
4.  `sample_status_lookup`: Maps material state (`available`, `consumed`, `destroyed`).
5.  `signature_meanings`: Defines legally binding signing intents (`author`, `reviewer`, `approver`).

---

## 7. Association Tables

These tables represent explicit M:M mappings, holding metadata describing the relationship.

1.  `user_roles`: Maps `users` to `roles` (Captures `is_primary`, `expires_at`, `assigned_by`).
2.  `role_permissions`: Maps `roles` to `permissions` (Captures `granted_at`, `granted_by`).
3.  `organization_users`: Maps `users` to their assigned `departments` and `teams`.
4.  `experiment_samples`: Links `experiments` to `samples` used or created during the procedure.

---

## 8. Audit Tables

1.  **`audit_logs`**: Capture database trigger actions. Includes JSONB values of the delta changes (`old_values` vs `new_values`) to support GxP audit requirements.
2.  **`login_histories`**: Audit trail for authentication events (success/failure, IP, OS, agent, country).
3.  **`password_histories`**: Stores historical passwords to enforce non-reuse complexity.

---

## 9. Compliance Tables

1.  **`electronic_signatures`**: Cryptographically locks approved versions using SHA-256 snapshot hashes.
2.  **`electronic_signature_profiles`**: Governs signing profiles (algorithms and certificate thumbprints).
3.  **`workflow_history`**: Tracks approval routes to prove execution sequences to FDA auditors.

---

## 10. AI Tables

1.  **`vector_embeddings`**: Vector chunk coordinates using pgvector for semantic index matches.
2.  **`ai_conversations`**: Tracks threads with ELN AI Agent.
3.  **`ai_messages`**: Stores question-answer memory context.

---

## 11. Data Flow Between Modules

```
[Authentication Flow]
Credentials input ──> Validate User ──> Create Session & Token ──> Log LoginHistory

[Notebook Sign-off Flow]
Draft Experiment ──> Submit ──> Freeze Version ──> Initiate Workflow Route ──> Sign Cryptographically ──> Write Audit Log
```

---

## 12. ER Relationship Summary Matrix

| Table A | Table B | Relationship | Primary FK Column | Cascading Rule |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `user_profiles` | 1:1 | `user_id` | ON DELETE CASCADE |
| `users` | `user_roles` | 1:N | `user_id` | ON DELETE CASCADE |
| `roles` | `user_roles` | 1:N | `role_id` | ON DELETE CASCADE |
| `experiments`| `experiment_versions` | 1:N | `experiment_id` | ON DELETE CASCADE |
| `experiment_versions`| `electronic_signatures`| 1:N | `entity_id` (Filtered) | ON DELETE RESTRICT |
| `locations` | `locations` | 1:N (Self) | `parent_id` | ON DELETE CASCADE |
| `samples` | `transfers` | 1:N | `sample_id` | ON DELETE RESTRICT |

---

## 13. Missing Tables Identified During Review

1.  **`instruments` & `instrument_runs`**: Critical for LIMS integration. Telemetry data from chromatography or mass spectrometers must feed directly to experiments.
2.  **`workflow_definitions` & `workflow_steps`**: Standard workflows require predefined routing schemas. Static tables are needed to map these rules.
3.  **`notifications`**: Required to alert users about document signatures, approvals, and system-wide messages.
4.  **`attachments`**: Captures raw molecular files (e.g., `.mol`, `.fasta`) and images linked to notebook drafts.

---

## 14. Recommended Improvements

*   **Row-Level Security (RLS):** Apply PostgreSQL RLS policies matching `tenant_id` to prevent cross-tenant queries at the database kernel level.
*   **Trigger-Based Auditing:** Shift audit record construction from application-level ORMs to database-level triggers to guarantee that raw SQL updates are recorded.
*   **JSONB Schema Validation:** Use `CHECK` constraints on JSONB metadata fields to validate key-value attributes before insertion.

---

## 15. Final Physical Database Design Approval Checklist

- [x] All primary keys use `UUID` with `gen_random_uuid()` to prevent ID guessing.
- [x] Every table contains audit columns: `created_at`, `updated_at`, `created_by`, `updated_by`.
- [x] Multi-tenant separation is enforced on master tables using non-nullable `tenant_id` links.
- [x] The `audit_logs` table is range-partitioned by month.
- [x] High-write audit tables reject `UPDATE` and `DELETE` commands via database rules.
- [x] Crucial lookups are indexed. GIN indexes are configured on JSONB parameters.
- [x] No business logic is embedded inside index definitions.
