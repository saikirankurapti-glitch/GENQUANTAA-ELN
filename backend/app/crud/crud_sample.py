import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from uuid import UUID

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
        *,
        obj_in: SampleCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Sample:
        """Create a new Sample record and log initial chain-of-custody event."""
        sample = Sample(
            tenant_id=tenant_id,
            experiment_id=obj_in.experiment_id,
            sample_type_id=obj_in.sample_type_id,
            location_id=obj_in.storage_location_id,
            owner_id=current_user_id,
            name=obj_in.sample_name,
            sample_code=obj_in.sample_code,
            barcode=obj_in.barcode,
            status=obj_in.status or "available",
            quantity=obj_in.quantity,
            unit=obj_in.unit,
            metadata_json=obj_in.metadata_json or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await sample.insert()

        # Initial chain of custody record
        if current_user_id:
            coc = SampleChainOfCustody(
                sample_id=sample.id,
                action="registered",
                user_id=current_user_id,
                notes="Initial sample registration into laboratory registry.",
                created_at=datetime.now(timezone.utc),
            )
            await coc.insert()

        return sample

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Sample]:
        """Fetch Sample by ID within tenant scope."""
        sample = await Sample.find_one(
            Sample.id == id,
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )
        return sample

    async def get_by_barcode(
        self, *, barcode: str, tenant_id: UUID
    ) -> Optional[Sample]:
        """Fetch Sample by barcode within tenant scope."""
        sample = await Sample.find_one(
            Sample.barcode == barcode.upper(),
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )
        return sample

    async def get_by_code(
        self, *, experiment_id: UUID, sample_code: str, tenant_id: UUID
    ) -> Optional[Sample]:
        """Fetch Sample by sample_code within experiment and tenant scope."""
        sample = await Sample.find_one(
            Sample.experiment_id == experiment_id,
            Sample.sample_code == sample_code.upper(),
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )
        return sample

    async def update(
        self,
        *,
        db_obj: Sample,
        obj_in: SampleUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Sample:
        """Update existing Sample attributes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        # mapped attributes
        mapping = {
            "sample_name": "name",
            "storage_location_id": "location_id"
        }
        for field, value in update_data.items():
            if field in mapping:
                setattr(db_obj, mapping[field], value)
            elif hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()

        if current_user_id:
            coc = SampleChainOfCustody(
                sample_id=db_obj.id,
                action="updated",
                user_id=current_user_id,
                notes=f"Sample updated. Status: {db_obj.status}, Quantity: {db_obj.quantity}{db_obj.unit}",
                created_at=datetime.now(timezone.utc),
            )
            await coc.insert()

        return db_obj

    async def archive(
        self, *, sample_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Sample]:
        """Archive a Sample."""
        sample = await self.get_by_id(id=sample_id, tenant_id=tenant_id)
        if not sample:
            return None

        sample.status = "archived"
        sample.updated_at = datetime.now(timezone.utc)
        await sample.save()
        return sample

    async def restore(
        self, *, sample_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Sample]:
        """Restore an archived Sample."""
        sample = await self.get_by_id(id=sample_id, tenant_id=tenant_id)
        if not sample:
            return None

        sample.status = "available"
        sample.updated_at = datetime.now(timezone.utc)
        await sample.save()
        return sample

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft-delete Sample."""
        sample = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not sample:
            return False

        sample.is_deleted = True
        sample.updated_at = datetime.now(timezone.utc)
        await sample.save()
        return True

    async def list_samples(
        self,
        *,
        tenant_id: UUID,
        filter_params: SampleFilter,
        pagination: SamplePagination
    ) -> Tuple[List[dict], int]:
        """List and search Samples with filtering and pagination."""
        query = Sample.find(
            Sample.tenant_id == tenant_id,
            Sample.is_deleted == False
        )

        if filter_params.experiment_id:
            query = query.find(Sample.experiment_id == filter_params.experiment_id)
        if filter_params.sample_type_id:
            query = query.find(Sample.sample_type_id == filter_params.sample_type_id)
        if filter_params.storage_location_id:
            query = query.find(Sample.location_id == filter_params.storage_location_id)
        if filter_params.status:
            query = query.find(Sample.status == filter_params.status)
        if filter_params.barcode:
            query = query.find(Sample.barcode == filter_params.barcode.upper())
        if filter_params.search:
            query = query.find({"$or": [
                {"sample_code": {"$regex": filter_params.search, "$options": "i"}},
                {"barcode": {"$regex": filter_params.search, "$options": "i"}},
                {"name": {"$regex": filter_params.search, "$options": "i"}},
            ]})

        total = await query.count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await query.sort(-Sample.created_at).skip(skip).limit(pagination.page_size).to_list()
        
        mapped_items = []
        for i in items:
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": i.tenant_id,
                "experiment_id": i.experiment_id,
                "sample_type_id": i.sample_type_id,
                "storage_location_id": i.location_id,
                "owner_id": i.owner_id,
                "sample_name": i.name,
                "sample_code": i.sample_code,
                "barcode": i.barcode,
                "status": i.status,
                "quantity": i.quantity,
                "unit": i.unit,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            })
            
        return mapped_items, total

    async def log_chain_of_custody(
        self,
        *,
        sample_id: UUID,
        action: str,
        user_id: UUID,
        remarks: Optional[str] = None
    ) -> SampleChainOfCustody:
        coc = SampleChainOfCustody(
            sample_id=sample_id,
            action=action,
            user_id=user_id,
            notes=remarks,
            created_at=datetime.now(timezone.utc),
        )
        await coc.insert()
        return coc

    async def get_chain_of_custody(
        self, *, sample_id: UUID
    ) -> List[SampleChainOfCustody]:
        return await SampleChainOfCustody.find(
            SampleChainOfCustody.sample_id == sample_id
        ).sort(-SampleChainOfCustody.created_at).to_list()

    async def add_attachment(
        self,
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
