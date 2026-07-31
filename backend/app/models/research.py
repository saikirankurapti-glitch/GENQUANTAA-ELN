from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.db.mixins import UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin
from app.db.enums import StudyStatus
from app.models.project import Project
from app.models.experiment import Experiment

class Study(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "studies"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    study_code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[StudyStatus] = mapped_column(default=StudyStatus.ACTIVE, nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

class ExperimentVersion(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "experiment_versions"

    experiment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
