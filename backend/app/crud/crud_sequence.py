import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sequence import (
    Sequence,
    SequenceAnalysisResult,
    SequenceAnnotation,
    SequenceAttachment,
    SequenceVersion,
)
from app.schemas.sequence import (
    SequenceAnnotationCreate,
    SequenceCreate,
    SequenceFilter,
    SequencePagination,
    SequenceUpdate,
    _compute_gc_content,
)

logger = logging.getLogger(__name__)


class SequenceRepository:
    """Async Repository for Sequence entities with strict tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: SequenceCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None,
    ) -> Sequence:
        """Create a new Sequence record and snapshot the first version."""
        seq_data = obj_in.sequence_data.upper()
        length = len(seq_data)
        gc = _compute_gc_content(obj_in.sequence_type, seq_data)

        seq = Sequence(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            experiment_id=obj_in.experiment_id,
            sample_id=obj_in.sample_id,
            sequence_code=obj_in.sequence_code,
            sequence_name=obj_in.sequence_name,
            sequence_type=obj_in.sequence_type,
            sequence_data=seq_data,
            length=length,
            gc_content=gc,
            molecular_weight=obj_in.molecular_weight,
            source=obj_in.source,
            status="active",
            version=1,
            metadata_json=obj_in.metadata_json,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(seq)
        await db.flush()

        # Snapshot version 1
        ver = SequenceVersion(
            sequence_id=seq.id,
            version_number=1,
            sequence_data=seq_data,
            length=length,
            gc_content=gc,
            change_summary="Initial version.",
            created_by=current_user_id,
        )
        db.add(ver)
        await db.commit()
        await db.refresh(seq)
        return seq

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: UUID,
        include_details: bool = False,
    ) -> Optional[Sequence]:
        """Fetch Sequence by ID within tenant scope."""
        stmt = select(Sequence).where(
            Sequence.id == id,
            Sequence.tenant_id == tenant_id,
            Sequence.is_deleted == False,
        )
        if include_details:
            stmt = stmt.options(
                selectinload(Sequence.seq_versions),
                selectinload(Sequence.annotations),
                selectinload(Sequence.attachments),
                selectinload(Sequence.analysis_results),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, sequence_code: str, tenant_id: UUID
    ) -> Optional[Sequence]:
        """Fetch Sequence by code within tenant scope."""
        stmt = select(Sequence).where(
            Sequence.sequence_code == sequence_code.upper(),
            Sequence.tenant_id == tenant_id,
            Sequence.is_deleted == False,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Sequence,
        obj_in: SequenceUpdate,
        current_user_id: Optional[UUID] = None,
    ) -> Sequence:
        """Update Sequence. If sequence_data changes, archive a new version."""
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"change_summary"})

        # If sequence_data is changing, validate and recompute metrics
        if "sequence_data" in update_data:
            raw = update_data["sequence_data"].upper()
            seq_type = update_data.get("sequence_type", db_obj.sequence_type)
            update_data["sequence_data"] = raw
            update_data["length"] = len(raw)
            update_data["gc_content"] = _compute_gc_content(seq_type, raw)

            # Increment version and snapshot
            new_version = db_obj.version + 1
            update_data["version"] = new_version
            ver = SequenceVersion(
                sequence_id=db_obj.id,
                version_number=new_version,
                sequence_data=raw,
                length=len(raw),
                gc_content=_compute_gc_content(seq_type, raw),
                change_summary=obj_in.change_summary or f"Updated to version {new_version}.",
                created_by=current_user_id,
            )
            db.add(ver)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def soft_delete(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None,
    ) -> bool:
        """Soft-delete a Sequence record."""
        seq = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not seq:
            return False
        seq.is_deleted = True
        seq.deleted_at = datetime.now(timezone.utc)
        seq.deleted_by = current_user_id
        db.add(seq)
        await db.commit()
        return True

    async def archive(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None,
    ) -> Optional[Sequence]:
        """Archive a Sequence."""
        seq = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not seq:
            return None
        seq.status = "archived"
        seq.archived_at = datetime.now(timezone.utc)
        seq.updated_by = current_user_id
        db.add(seq)
        await db.commit()
        await db.refresh(seq)
        return seq

    async def restore(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None,
    ) -> Optional[Sequence]:
        """Restore an archived Sequence."""
        seq = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not seq:
            return None
        seq.status = "active"
        seq.archived_at = None
        seq.updated_by = current_user_id
        db.add(seq)
        await db.commit()
        await db.refresh(seq)
        return seq

    async def list_sequences(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: SequenceFilter,
        pagination: SequencePagination,
    ) -> Tuple[List[Sequence], int]:
        """List and search Sequences with filtering and pagination."""
        query = select(Sequence).where(
            Sequence.tenant_id == tenant_id,
            Sequence.is_deleted == False,
        )
        if filter_params.sequence_type:
            query = query.where(Sequence.sequence_type == filter_params.sequence_type.upper())
        if filter_params.status:
            query = query.where(Sequence.status == filter_params.status)
        if filter_params.experiment_id:
            query = query.where(Sequence.experiment_id == filter_params.experiment_id)
        if filter_params.sample_id:
            query = query.where(Sequence.sample_id == filter_params.sample_id)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    Sequence.sequence_code.ilike(pattern),
                    Sequence.sequence_name.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one() or 0

        sort_col = getattr(Sequence, pagination.sort_by, Sequence.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)
        items = list((await db.execute(query)).scalars().all())
        return items, total

    async def add_annotation(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        ann_in: SequenceAnnotationCreate,
        current_user_id: Optional[UUID] = None,
    ) -> SequenceAnnotation:
        """Add a functional annotation to a sequence region."""
        ann = SequenceAnnotation(
            sequence_id=sequence_id,
            annotation_type=ann_in.annotation_type,
            label=ann_in.label,
            start_position=ann_in.start_position,
            end_position=ann_in.end_position,
            strand=ann_in.strand,
            notes=ann_in.notes,
            created_by=current_user_id,
        )
        db.add(ann)
        await db.commit()
        await db.refresh(ann)
        return ann

    async def save_analysis_result(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        analysis_type: str,
        tool_name: Optional[str],
        tool_version: Optional[str],
        result_summary: Optional[str],
        result_json: dict,
        performed_by: Optional[UUID],
    ) -> SequenceAnalysisResult:
        """Persist a sequence analysis result."""
        result = SequenceAnalysisResult(
            sequence_id=sequence_id,
            analysis_type=analysis_type,
            tool_name=tool_name,
            tool_version=tool_version,
            result_summary=result_summary,
            result_json=result_json,
            performed_by=performed_by,
        )
        db.add(result)
        await db.commit()
        await db.refresh(result)
        return result

    async def list_analysis_results(
        self, db: AsyncSession, *, sequence_id: UUID
    ) -> List[SequenceAnalysisResult]:
        """Fetch all analysis results for a sequence."""
        stmt = (
            select(SequenceAnalysisResult)
            .where(SequenceAnalysisResult.sequence_id == sequence_id)
            .order_by(SequenceAnalysisResult.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())


sequence_repo = SequenceRepository()
