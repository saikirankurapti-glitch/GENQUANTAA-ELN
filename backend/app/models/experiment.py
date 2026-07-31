from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, ForeignKey, Uuid, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin
from app.db.enums import ExperimentStatus

class Experiment(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "experiments"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    experiment_number: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(default=ExperimentStatus.DRAFT, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

class ExperimentCollaborator(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "experiment_collaborators"

    experiment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="collaborator", nullable=False)

class ExperimentAttachment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "experiment_attachments"

    experiment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
