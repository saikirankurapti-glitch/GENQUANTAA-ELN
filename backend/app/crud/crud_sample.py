import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sample import (
    Sample,
    SampleAttachment,
    SampleChainOfCustody,
    SampleStorageLocation,
    SampleType,
)
from app.schemas.sample import SampleCreate, SampleFilter, SamplePagination, SampleUpdate

logger = logging.getLogger(__name__)


class SampleRepository:
    """Async Repository handling data access for Sample entities with strict tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: SampleCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Sample:
        """Create a new Sample record and log initial chain-of-custody event."""
        sample = Sample(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            experiment_id=obj_in.experiment_id,
            sample_type_id=obj_in.sample_type_id,
            storage_location_id=obj_in.storage_location_id,
            parent_sample_id=obj_in.parent_sample_id,
            sample_code=obj_in.sample_code,
            barcode=obj_in.barcode,
            sample_name=obj_in.sample_name,
            quantity=obj_in.quantity,
            unit=obj_in.unit,
            concentration=obj_in.concentration,
            storage_temperature=obj_in.storage_temperature,
            collection_date=obj_in.collection_date,
            expiry_date=obj_in.expiry_date,
            status=obj_in.status,
            metadata_json=obj_in.metadata_json,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(sample)
        await db.flush()

        # Initial chain of custody record
        if current_user_id:
            coc = SampleChainOfCustody(
                sample_id=sample.id,
                action="registered",
                custodian_id=current_user_id,
                remarks="Initial sample registration into laboratory registry.",
            )
            db.add(coc)

        await db.commit()
        await db.refresh(sample)
        return sample

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Sample]:
        """Fetch Sample by ID within tenant scope."""
        stmt = select(Sample).where(
            Sample.id == id,
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(Sample.chain_of_custody),
                selectinload(Sample.attachments),
                selectinload(Sample.sample_type),
                selectinload(Sample.storage_location),
                selectinload(Sample.experiment),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_barcode(
        self, db: AsyncSession, *, barcode: str, tenant_id: UUID
    ) -> Optional[Sample]:
        """Fetch Sample by barcode within tenant scope."""
        stmt = select(Sample).where(
            Sample.barcode == barcode.upper(),
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, experiment_id: UUID, sample_code: str, tenant_id: UUID
    ) -> Optional[Sample]:
        """Fetch Sample by sample_code within experiment and tenant scope."""
        stmt = select(Sample).where(
            Sample.experiment_id == experiment_id,
            Sample.sample_code == sample_code.upper(),
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Sample,
        obj_in: SampleUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Sample:
        """Update existing Sample attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)

        if current_user_id:
            coc = SampleChainOfCustody(
                sample_id=db_obj.id,
                action="updated",
                custodian_id=current_user_id,
                remarks=f"Sample updated. Status: {db_obj.status}, Quantity: {db_obj.quantity}{db_obj.unit}",
            )
            db.add(coc)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def archive(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Sample]:
        """Archive a Sample."""
        sample = await self.get_by_id(db, id=sample_id, tenant_id=tenant_id)
        if not sample:
            return None

        sample.is_archived = True
        sample.archived_at = datetime.now(timezone.utc)
        sample.status = "archived"
        sample.updated_by = current_user_id
        db.add(sample)
        await db.commit()
        await db.refresh(sample)
        return sample

    async def restore(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Sample]:
        """Restore an archived Sample."""
        sample = await self.get_by_id(db, id=sample_id, tenant_id=tenant_id)
        if not sample:
            return None

        sample.is_archived = False
        sample.archived_at = None
        sample.status = "available"
        sample.updated_by = current_user_id
        db.add(sample)
        await db.commit()
        await db.refresh(sample)
        return sample

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete Sample."""
        sample = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not sample:
            return False

        sample.is_deleted = True
        sample.deleted_at = datetime.now(timezone.utc)
        sample.deleted_by = current_user_id
        db.add(sample)
        await db.commit()
        return True

    async def list_samples(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: SampleFilter,
        pagination: SamplePagination
    ) -> Tuple[List[Sample], int]:
        """List and search Samples with filtering and pagination."""
        query = select(Sample).where(
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )

        if filter_params.experiment_id:
            query = query.where(Sample.experiment_id == filter_params.experiment_id)
        if filter_params.sample_type_id:
            query = query.where(Sample.sample_type_id == filter_params.sample_type_id)
        if filter_params.storage_location_id:
            query = query.where(Sample.storage_location_id == filter_params.storage_location_id)
        if filter_params.status:
            query = query.where(Sample.status == filter_params.status)
        if filter_params.barcode:
            query = query.where(Sample.barcode == filter_params.barcode.upper())
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    Sample.sample_code.ilike(pattern),
                    Sample.barcode.ilike(pattern),
                    Sample.sample_name.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(Sample, pagination.sort_by, Sample.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def log_chain_of_custody(
        self,
        db: AsyncSession,
        *,
        sample_id: UUID,
        action: str,
        custodian_id: UUID,
        remarks: Optional[str] = None
    ) -> SampleChainOfCustody:
        """Log a new chain-of-custody audit event."""
        coc = SampleChainOfCustody(
            sample_id=sample_id,
            action=action,
            custodian_id=custodian_id,
            remarks=remarks,
        )
        db.add(coc)
        await db.commit()
        await db.refresh(coc)
        return coc

    async def get_chain_of_custody_history(
        self, db: AsyncSession, *, sample_id: UUID
    ) -> List[SampleChainOfCustody]:
        """Fetch chain of custody history for a sample."""
        stmt = (
            select(SampleChainOfCustody)
            .where(SampleChainOfCustody.sample_id == sample_id)
            .order_by(SampleChainOfCustody.performed_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_attachment(
        self,
        db: AsyncSession,
        *,
        sample_id: UUID,
        filename: str,
        blob_path: str,
        mime_type: Optional[str],
        file_size: int,
        checksum: str,
        current_user_id: Optional[UUID] = None
    ) -> SampleAttachment:
        """Add an attachment to a Sample."""
        attachment = SampleAttachment(
            sample_id=sample_id,
            filename=filename,
            blob_path=blob_path,
            mime_type=mime_type,
            file_size=file_size,
            checksum=checksum,
            uploaded_by=current_user_id,
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        return attachment


sample_repo = SampleRepository()
