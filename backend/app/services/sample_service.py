import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_experiment import experiment_repo
from app.crud.crud_sample import sample_repo
from app.models.identity import User
from app.models.sample import Sample, SampleAttachment, SampleChainOfCustody
from app.schemas.sample import SampleCreate, SampleFilter, SamplePagination, SampleUpdate

logger = logging.getLogger(__name__)


# Domain Exceptions
class SampleNotFound(Exception):
    pass


class DuplicateSampleCode(Exception):
    pass


class DuplicateSampleBarcode(Exception):
    pass


class ExperimentArchivedOrNotFound(Exception):
    pass


class SampleArchivedError(Exception):
    pass


class InvalidSampleQuantityError(Exception):
    pass


class SampleService:
    """Service layer enforcing sample registry rules, barcode uniqueness, and chain of custody tracking."""

    async def create_sample(
        self, db: AsyncSession, *, obj_in: SampleCreate, tenant_id: UUID, current_user: User
    ) -> Sample:
        """Register a new sample ensuring experiment is active and barcode/code are unique."""
        # 1. Validate Parent Experiment
        exp = await experiment_repo.get_by_id(db, id=obj_in.experiment_id, tenant_id=tenant_id)
        if not exp:
            raise ExperimentArchivedOrNotFound(f"Parent Experiment {obj_in.experiment_id} not found.")
        if exp.is_archived:
            raise ExperimentArchivedOrNotFound("Cannot register a sample under an archived Experiment.")

        # 2. Validate Code Uniqueness within Experiment
        existing_code = await sample_repo.get_by_code(
            db, experiment_id=obj_in.experiment_id, sample_code=obj_in.sample_code, tenant_id=tenant_id
        )
        if existing_code:
            raise DuplicateSampleCode(
                f"Sample code '{obj_in.sample_code}' already exists in Experiment {obj_in.experiment_id}."
            )

        # 3. Validate Barcode Uniqueness within Tenant
        existing_barcode = await sample_repo.get_by_barcode(db, barcode=obj_in.barcode, tenant_id=tenant_id)
        if existing_barcode:
            raise DuplicateSampleBarcode(f"Sample barcode '{obj_in.barcode}' already exists in this tenant.")

        # 4. Validate Quantity
        if obj_in.quantity < 0:
            raise InvalidSampleQuantityError("Sample quantity cannot be negative.")

        sample = await sample_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"SampleService: Registered sample '{sample.sample_code}' with barcode '{sample.barcode}' (ID: {sample.id})")
        return sample

    async def get_sample(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Sample:
        """Fetch sample by ID or raise SampleNotFound."""
        sample = await sample_repo.get_by_id(
            db, id=sample_id, tenant_id=tenant_id, include_details=include_details
        )
        if not sample:
            raise SampleNotFound(f"Sample {sample_id} not found.")
        return sample

    async def get_by_barcode(
        self, db: AsyncSession, *, barcode: str, tenant_id: UUID
    ) -> Sample:
        """Fetch sample by barcode or raise SampleNotFound."""
        sample = await sample_repo.get_by_barcode(db, barcode=barcode, tenant_id=tenant_id)
        if not sample:
            raise SampleNotFound(f"Sample with barcode '{barcode}' not found.")
        return sample

    async def update_sample(
        self,
        db: AsyncSession,
        *,
        sample_id: UUID,
        obj_in: SampleUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Sample:
        """Update sample attributes and log chain-of-custody event."""
        sample = await self.get_sample(db, sample_id=sample_id, tenant_id=tenant_id)
        if sample.is_archived:
            raise SampleArchivedError("Cannot update an archived sample. Restore it first.")

        if obj_in.quantity is not None and obj_in.quantity < 0:
            raise InvalidSampleQuantityError("Sample quantity cannot be negative.")

        updated_sample = await sample_repo.update(
            db, db_obj=sample, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"SampleService: Updated sample {sample_id}")
        return updated_sample

    async def archive_sample(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID, current_user: User
    ) -> Sample:
        """Archive a sample."""
        sample = await self.get_sample(db, sample_id=sample_id, tenant_id=tenant_id)
        if sample.is_archived:
            return sample

        archived = await sample_repo.archive(
            db, sample_id=sample_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"SampleService: Archived sample {sample_id}")
        return archived

    async def restore_sample(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID, current_user: User
    ) -> Sample:
        """Restore an archived sample."""
        sample = await self.get_sample(db, sample_id=sample_id, tenant_id=tenant_id)
        if not sample.is_archived:
            return sample

        restored = await sample_repo.restore(
            db, sample_id=sample_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"SampleService: Restored sample {sample_id}")
        return restored

    async def delete_sample(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete a sample."""
        success = await sample_repo.soft_delete(
            db, id=sample_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise SampleNotFound(f"Sample {sample_id} not found.")
        logger.info(f"SampleService: Soft deleted sample {sample_id}")
        return True

    async def list_samples(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: SampleFilter,
        pagination: SamplePagination
    ) -> Tuple[List[Sample], int]:
        """List samples with filtering and pagination."""
        return await sample_repo.list_samples(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

    async def get_chain_of_custody(
        self, db: AsyncSession, *, sample_id: UUID, tenant_id: UUID
    ) -> List[SampleChainOfCustody]:
        """Fetch chain of custody history for a sample."""
        await self.get_sample(db, sample_id=sample_id, tenant_id=tenant_id, include_details=False)
        return await sample_repo.get_chain_of_custody_history(db, sample_id=sample_id)


sample_service = SampleService()
