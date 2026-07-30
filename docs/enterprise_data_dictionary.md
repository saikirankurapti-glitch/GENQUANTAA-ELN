# Enterprise Data Dictionary: Identity Management Module

This document defines the physical data dictionary for the 12 tables constituting the Identity Management module of the ELN/LIMS platform. It provides precise specifications for PostgreSQL data types, nullability rules, constraints, defaults, and data definitions mapped to GxP and FDA 21 CFR Part 11 guidelines.

---

## 1. Table: `users`
*   **Schema**: `identity`
*   **Purpose**: Stores authenticatable user entities.
*   **Multi-Tenancy Isolation**: Scoped by `tenant_id`.
*   **Audit Trail**: Audited via trigger (INSERT, UPDATE, DELETE).
*   **Soft Delete**: Implemented via `is_deleted`.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY, Index | Unique identifier for each user. |
| `tenant_id` | `UUID` | NO | - | FK to `tenants.id` ON DELETE CASCADE, Index | Multi-tenant isolation key. |
| `organization_id` | `UUID` | YES | - | FK to `organizations.id` ON DELETE SET NULL, Index | Affiliated organization identifier. |
| `employee_id` | `VARCHAR(64)` | YES | - | Index | Corporate HR identification code. |
| `username` | `VARCHAR(128)` | NO | - | UNIQUE (`tenant_id`, `username`), Index | Case-insensitive login identifier. |
| `email` | `VARCHAR(255)` | NO | - | UNIQUE (`tenant_id`, `email`), Index | Corporate email address. Must match email regex. |
| `first_name` | `VARCHAR(128)` | NO | - | - | User's legal first name. |
| `last_name` | `VARCHAR(128)` | NO | - | - | User's legal last name. |
| `display_name` | `VARCHAR(255)` | YES | - | - | Preferred display name. |
| `phone_number` | `VARCHAR(32)` | YES | - | - | E.164 formatted telephone number. |
| `password_hash` | `VARCHAR(255)` | NO | - | - | Argon2id cryptographically hashed password. |
| `password_changed_at` | `TIMESTAMPTZ` | YES | - | - | Timestamp when password was last set. Used for age limits. |
| `must_change_password`| `BOOLEAN` | NO | `FALSE` | - | Forces password reset on next successful login. |
| `email_verified` | `BOOLEAN` | NO | `FALSE` | - | Indicates if email ownership is verified. |
| `phone_verified` | `BOOLEAN` | NO | `FALSE` | - | Indicates if phone ownership is verified. |
| `is_active` | `BOOLEAN` | NO | `TRUE` | Index | System state flag. Active users can log in. |
| `is_locked` | `BOOLEAN` | NO | `FALSE` | Index | Brute-force account lock state. |
| `failed_login_attempts`| `INTEGER` | NO | `0` | CHECK (`failed_login_attempts` >= 0) | Sequential failed auth counters. Resets on success. |
| `locked_until` | `TIMESTAMPTZ` | YES | - | - | Timestamp when temporary account lock expires. |
| `status` | `VARCHAR(32)` | NO | `'active'` | CHECK (`status` IN ('active', 'inactive', 'suspended')) | Lifecycle status domain. |
| `created_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Audit field: Timestamp of record creation. |
| `updated_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Audit field: Timestamp of last record update. |
| `created_by` | `UUID` | YES | - | - | Audit field: User UUID who created this record. |
| `updated_by` | `UUID` | YES | - | - | Audit field: User UUID who last updated this record. |
| `is_deleted` | `BOOLEAN` | NO | `FALSE` | Index | Soft delete flag (FDA requirement to prevent hard delete). |
| `deleted_at` | `TIMESTAMPTZ` | YES | - | - | Soft delete audit timestamp. |
| `deleted_by` | `UUID` | YES | - | - | Soft delete author identifier. |

---

## 2. Table: `user_profiles`
*   **Schema**: `identity`
*   **Purpose**: Stores non-security user profile details.
*   **Multi-Tenancy Isolation**: Scoped implicitly via User association.
*   **Soft Delete**: Inherits from `users`.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique profile record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, UNIQUE, Index | Core user mapping (enforces 1-to-1 relationship). |
| `date_of_birth` | `DATE` | YES | - | - | Date of birth. |
| `gender` | `VARCHAR(32)` | YES | - | - | Gender preference. |
| `department` | `VARCHAR(128)` | YES | - | - | Structural department label. |
| `designation` | `VARCHAR(128)` | YES | - | - | Job title / Role description. |
| `location` | `VARCHAR(255)` | YES | - | - | Physical corporate facility/location. |
| `time_zone` | `VARCHAR(64)` | YES | `'UTC'` | - | Time zone identifier (IANA format). |
| `language` | `VARCHAR(16)` | YES | `'en'` | - | Language preference code (ISO 639-1). |
| `avatar_url` | `VARCHAR(512)` | YES | - | - | Storage URL link for profile avatar. |
| `biography` | `TEXT` | YES | - | - | Professional background narrative text. |

---

## 3. Table: `user_roles`
*   **Schema**: `identity`
*   **Purpose**: Explicit association table assigning roles to users.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique assignment record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Targeted user identifier. |
| `role_id` | `UUID` | NO | - | FK to `roles.id` ON DELETE CASCADE, Index | Assigned role identifier. |
| `assigned_by` | `UUID` | YES | - | FK to `users.id` ON DELETE SET NULL | UUID of administrator performing assignment. |
| `assigned_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Timestamp when assignment was recorded. |
| `expires_at` | `TIMESTAMPTZ` | YES | - | - | Expiration timestamp for temporary roles. |
| `is_primary` | `BOOLEAN` | NO | `FALSE` | - | Indicates user's default role for session routing. |
| `is_active` | `BOOLEAN` | NO | `TRUE` | - | Active assignment toggle. |

*   **Unique Constraint**: `uq_user_roles_user_role` (`user_id`, `role_id`)

---

## 4. Table: `refresh_tokens`
*   **Schema**: `identity`
*   **Purpose**: Tracks long-lived refresh tokens for OAuth2 rotation.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique token record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Token owner. |
| `token_hash` | `VARCHAR(255)` | NO | - | UNIQUE, Index | Cryptographic hash (SHA-256) of the refresh token. |
| `issued_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Generation timestamp. |
| `expires_at` | `TIMESTAMPTZ` | NO | - | - | Expiration timestamp. |
| `revoked_at` | `TIMESTAMPTZ` | YES | - | - | Revocation timestamp (if rotated early). |
| `device_name` | `VARCHAR(255)` | YES | - | - | Hardware label of the logging device. |
| `ip_address` | `VARCHAR(45)` | YES | - | - | IP address (v4 or v6) that requested the token. |

*   **Check Constraint**: `ck_refresh_tokens_expiry` (`expires_at` > `issued_at`)

---

## 5. Table: `user_sessions`
*   **Schema**: `identity`
*   **Purpose**: Tracks active user sessions.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique session record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Connected user. |
| `refresh_token_id` | `UUID` | YES | - | FK to `refresh_tokens.id` ON DELETE SET NULL, UNIQUE | Refresh token validating this session. |
| `session_token_hash`| `VARCHAR(255)` | NO | - | UNIQUE, Index | SHA-256 hash of active session token. |
| `device_name` | `VARCHAR(255)` | YES | - | - | User hardware device name. |
| `browser` | `VARCHAR(128)` | YES | - | - | Web browser signature label. |
| `operating_system` | `VARCHAR(128)` | YES | - | - | Client operating system signature. |
| `ip_address` | `VARCHAR(45)` | YES | - | - | IP address of current activity. |
| `user_agent` | `VARCHAR(512)` | YES | - | - | Raw User-Agent string. |
| `last_activity` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Timestamp of last API interaction. |
| `expires_at` | `TIMESTAMPTZ` | NO | - | - | Session absolute expiration timestamp. |
| `is_revoked` | `BOOLEAN` | NO | `FALSE` | - | Active session termination toggle. |

---

## 6. Table: `login_histories`
*   **Schema**: `identity`
*   **Purpose**: Immutable log auditing all authentication attempts.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique audit record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Auth subject. |
| `login_time` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Timestamp of authentication event. |
| `logout_time` | `TIMESTAMPTZ` | YES | - | - | Timestamp of logout event. |
| `ip_address` | `VARCHAR(45)` | YES | - | - | Source IP address. |
| `device` | `VARCHAR(255)` | YES | - | - | Target client device name. |
| `browser` | `VARCHAR(128)` | YES | - | - | Target client web browser name. |
| `operating_system` | `VARCHAR(128)` | YES | - | - | Target client OS. |
| `country` | `VARCHAR(128)` | YES | - | - | Resolved geolocation country code. |
| `city` | `VARCHAR(128)` | YES | - | - | Resolved geolocation city name. |
| `status` | `VARCHAR(32)` | NO | - | CHECK (`status` IN ('success', 'failed')) | Authentication result status. |
| `failure_reason` | `VARCHAR(255)` | YES | - | - | Reason explaining failed logins. |

---

## 7. Table: `password_histories`
*   **Schema**: `identity`
*   **Purpose**: Retains historical password hashes to prevent password re-use.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique history record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Associated user. |
| `password_hash` | `VARCHAR(255)` | NO | - | - | Argon2id hash of the historical password. |
| `changed_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Timestamp when this password was set. |

---

## 8. Table: `mfa_devices`
*   **Schema**: `identity`
*   **Purpose**: Manages user Multi-Factor Authentication setups.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique device record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Device owner. |
| `device_name` | `VARCHAR(255)` | NO | `'Primary MFA Device'` | - | User-facing identifier name. |
| `type` | `VARCHAR(32)` | NO | `'totp'` | - | MFA token type domain (e.g. 'totp'). |
| `secret` | `VARCHAR(255)` | NO | - | - | Encrypted MFA key seed value. |
| `verified` | `BOOLEAN` | NO | `FALSE` | - | Verification state indicator. |
| `verified_at` | `TIMESTAMPTZ` | YES | - | - | Timestamp of initial verification. |
| `last_used` | `TIMESTAMPTZ` | YES | - | - | Timestamp when token was last verified. |

---

## 9. Table: `api_keys`
*   **Schema**: `identity`
*   **Purpose**: Authenticates machine-to-machine integrations.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique key record identifier. |
| `tenant_id` | `UUID` | NO | - | FK to `tenants.id` ON DELETE CASCADE, Index | Tenant namespace scoping link. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | User owner acting for integration actions. |
| `name` | `VARCHAR(128)` | NO | - | - | Functional naming description. |
| `hashed_key` | `VARCHAR(255)` | NO | - | UNIQUE, Index | SHA-256 hash of API key string. |
| `expires_at` | `TIMESTAMPTZ` | YES | - | - | Expiration timestamp. |
| `last_used` | `TIMESTAMPTZ` | YES | - | - | Timestamp of last operational API call. |
| `is_active` | `BOOLEAN` | NO | `TRUE` | - | Key enable/disable state toggle. |
| `created_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Audit field: key generation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Audit field: key modification timestamp. |

---

## 10. Table: `trusted_devices`
*   **Schema**: `identity`
*   **Purpose**: Registers recognized client devices to bypass secondary MFA requirements.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique device registry identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, Index | Authorized user reference. |
| `device_identifier` | `VARCHAR(255)` | NO | - | UNIQUE, Index | Fingerprint cryptographic ID of the device hardware. |
| `device_name` | `VARCHAR(255)` | YES | - | - | Human readable name. |
| `browser` | `VARCHAR(128)` | YES | - | - | User-agent browser name. |
| `operating_system` | `VARCHAR(128)` | YES | - | - | Operating system fingerprint. |
| `ip_address` | `VARCHAR(45)` | YES | - | - | IP address registration location. |
| `trusted_since` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Timestamp trust authorization was granted. |
| `last_seen` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Timestamp of last api session usage. |

---

## 11. Table: `user_preferences`
*   **Schema**: `identity`
*   **Purpose**: UI and UX user preference configurations.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique preferences record identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, UNIQUE, Index | Core user mapping link. |
| `theme` | `VARCHAR(32)` | NO | `'light'` | - | Selected interface layout style. |
| `language` | `VARCHAR(16)` | NO | `'en'` | - | Preferred locale code. |
| `time_zone` | `VARCHAR(64)` | NO | `'UTC'` | - | Selected timezone database string. |
| `notification_settings`| `JSON` | NO | `'{}'` | - | JSON structure configuring alerts channels. |

---

## 12. Table: `electronic_signature_profiles`
*   **Schema**: `identity`
*   **Purpose**: Holds legal signature capabilities and profiles for GxP digital sign-offs.

### Column Definitions
| Column Name | PostgreSQL Type | Nullable | Default Value | Keys & Constraints | Business Description / Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | NO | `gen_random_uuid()` | PRIMARY KEY | Unique signature profile identifier. |
| `user_id` | `UUID` | NO | - | FK to `users.id` ON DELETE CASCADE, UNIQUE, Index | Signing user link. |
| `signature_meaning` | `VARCHAR(255)` | YES | - | - | Default legal intent text (e.g. 'Author'). |
| `signature_algorithm` | `VARCHAR(64)` | YES | - | - | Cryptographic algorithm configuration. |
| `certificate_thumbprint`| `VARCHAR(255)`| YES | - | - | Thumbprint verifying user certificate validity. |
| `enabled` | `BOOLEAN` | NO | `TRUE` | - | Signature profile active state flag. |
| `created_at` | `TIMESTAMPTZ` | NO | `clock_timestamp()` | - | Generation timestamp. |
