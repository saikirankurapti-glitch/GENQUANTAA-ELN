from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin
from app.db.enums import OrganizationStatus

class Organization(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[OrganizationStatus] = mapped_column(default=OrganizationStatus.ACTIVE, nullable=False)

class Department(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "departments"

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

class Team(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "teams"

    department_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

class OrganizationUser(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "organization_users"

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
