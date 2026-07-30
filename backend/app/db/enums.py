import enum
import sqlalchemy

# Enterprise Fix: Force SQLAlchemy to use the Enum values instead of the Enum names.
# This ensures that PostgreSQL receives 'active' (value) instead of 'ACTIVE' (name),
# aligning Python Enum values perfectly with the PostgreSQL ENUM schema constraints.
_original_enum_init = sqlalchemy.Enum.__init__
def _new_enum_init(self, *enums, **kw):
    if 'values_callable' not in kw:
        kw['values_callable'] = lambda obj: [e.value for e in obj]
    _original_enum_init(self, *enums, **kw)
sqlalchemy.Enum.__init__ = _new_enum_init

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class ProjectStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class RoleStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class OrganizationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class StudyStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SampleStatus(str, enum.Enum):
    AVAILABLE = "available"
    CONSUMED = "consumed"
    DESTROYED = "destroyed"

class TransactionType(str, enum.Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    TRANSFER = "transfer"
    CONSUME = "consume"

class SignatureStatus(str, enum.Enum):
    VALID = "valid"
    REVOKED = "revoked"

class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class ApprovalType(str, enum.Enum):
    SINGLE = "single"
    UNANIMOUS = "unanimous"
    MAJORITY = "majority"

class WorkflowAction(str, enum.Enum):
    INITIATE = "initiate"
    APPROVE = "approve"
    REJECT = "reject"
    REVOKE = "revoke"