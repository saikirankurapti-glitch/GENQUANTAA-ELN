import logging
from io import StringIO
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_sequence import sequence_repo
from app.models.identity import User
from app.models.sequence import Sequence, SequenceAnalysisResult, SequenceAnnotation
from app.schemas.sequence import (
    FastaRecord,
    FastaUploadResponse,
    SequenceAnnotationCreate,
    SequenceCreate,
    SequenceFilter,
    SequencePagination,
    SequenceUpdate,
    _validate_sequence_alphabet,
    _compute_gc_content,
)

logger = logging.getLogger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────

class SequenceNotFound(Exception):
    pass


class DuplicateSequenceCode(Exception):
    pass


class InvalidSequenceAlphabet(Exception):
    pass


class SequenceArchivedError(Exception):
    pass


# ── FASTA parser ───────────────────────────────────────────────────────────────

def parse_fasta(fasta_text: str) -> List[FastaRecord]:
    """Parse raw FASTA text into a list of FastaRecord objects."""
    records: List[FastaRecord] = []
    current_header: Optional[str] = None
    current_seq_lines: List[str] = []

    for line in StringIO(fasta_text):
        line = line.rstrip()
        if not line:
            continue
        if line.startswith(">"):
            if current_header is not None:
                records.append(
                    FastaRecord(header=current_header, sequence_data="".join(current_seq_lines))
                )
            current_header = line[1:].strip()
            current_seq_lines = []
        else:
            current_seq_lines.append(line.strip())

    if current_header is not None:
        records.append(
            FastaRecord(header=current_header, sequence_data="".join(current_seq_lines))
        )
    return records


# ── Service ────────────────────────────────────────────────────────────────────

class SequenceService:
    """Service layer enforcing biological validation, GC computation, versioning, and uniqueness rules."""

    async def create_sequence(
        self,
        db: AsyncSession,
        *,
        obj_in: SequenceCreate,
        tenant_id: UUID,
        current_user: User,
    ) -> Sequence:
        """Register a new sequence after uniqueness and alphabet validation."""
        if await sequence_repo.get_by_code(db, sequence_code=obj_in.sequence_code, tenant_id=tenant_id):
            raise DuplicateSequenceCode(
                f"Sequence code '{obj_in.sequence_code}' already exists in this tenant workspace."
            )
        seq = await sequence_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"SequenceService: Registered '{seq.sequence_code}' [{seq.sequence_type}] (ID: {seq.id})")
        return seq

    async def get_sequence(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        tenant_id: UUID,
        include_details: bool = True,
    ) -> Sequence:
        """Fetch sequence by ID or raise SequenceNotFound."""
        seq = await sequence_repo.get_by_id(
            db, id=sequence_id, tenant_id=tenant_id, include_details=include_details
        )
        if not seq:
            raise SequenceNotFound(f"Sequence {sequence_id} not found.")
        return seq

    async def update_sequence(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        obj_in: SequenceUpdate,
        tenant_id: UUID,
        current_user: User,
    ) -> Sequence:
        """Update a sequence; validate alphabet if sequence_data is changing."""
        seq = await self.get_sequence(db, sequence_id=sequence_id, tenant_id=tenant_id, include_details=False)
        if seq.status == "archived":
            raise SequenceArchivedError("Cannot update an archived sequence.")

        # Validate new sequence data against the (possibly updated) type
        if obj_in.sequence_data:
            seq_type = (obj_in.sequence_type or seq.sequence_type).upper()
            try:
                obj_in.sequence_data = _validate_sequence_alphabet(seq_type, obj_in.sequence_data)
            except ValueError as e:
                raise InvalidSequenceAlphabet(str(e))

        return await sequence_repo.update(
            db, db_obj=seq, obj_in=obj_in, current_user_id=current_user.id
        )

    async def delete_sequence(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        tenant_id: UUID,
        current_user: User,
    ) -> bool:
        """Soft-delete a sequence."""
        success = await sequence_repo.soft_delete(
            db, id=sequence_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise SequenceNotFound(f"Sequence {sequence_id} not found.")
        return True

    async def list_sequences(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: SequenceFilter,
        pagination: SequencePagination,
    ) -> Tuple[List[Sequence], int]:
        """List sequences with filtering and pagination."""
        return await sequence_repo.list_sequences(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

    async def add_annotation(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        ann_in: SequenceAnnotationCreate,
        tenant_id: UUID,
        current_user: User,
    ) -> SequenceAnnotation:
        """Add a residue-level annotation to a sequence."""
        await self.get_sequence(db, sequence_id=sequence_id, tenant_id=tenant_id, include_details=False)
        return await sequence_repo.add_annotation(
            db, sequence_id=sequence_id, ann_in=ann_in, current_user_id=current_user.id
        )

    async def list_analysis_results(
        self,
        db: AsyncSession,
        *,
        sequence_id: UUID,
        tenant_id: UUID,
    ) -> List[SequenceAnalysisResult]:
        """Fetch analysis results for a sequence."""
        await self.get_sequence(db, sequence_id=sequence_id, tenant_id=tenant_id, include_details=False)
        return await sequence_repo.list_analysis_results(db, sequence_id=sequence_id)

    async def upload_fasta(
        self,
        db: AsyncSession,
        *,
        fasta_text: str,
        sequence_type: str,
        organization_id: UUID,
        tenant_id: UUID,
        current_user: User,
        experiment_id: Optional[UUID] = None,
        sample_id: Optional[UUID] = None,
    ) -> FastaUploadResponse:
        """
        Parse a FASTA text block and bulk-register all valid records.
        Returns a summary of registered/failed counts.
        """
        records = parse_fasta(fasta_text)
        registered = 0
        failed = 0
        errors: List[str] = []

        for i, record in enumerate(records):
            # Derive code from FASTA header (first token)
            raw_code = record.header.split()[0][:64].upper().replace("|", "-")
            seq_code = raw_code if raw_code else f"FASTA-{i+1}"

            try:
                validated_data = _validate_sequence_alphabet(sequence_type, record.sequence_data)
            except ValueError as e:
                failed += 1
                errors.append(f"Record '{record.header}': {e}")
                continue

            # Skip duplicate codes silently (or record error)
            if await sequence_repo.get_by_code(db, sequence_code=seq_code, tenant_id=tenant_id):
                failed += 1
                errors.append(f"Record '{record.header}': sequence_code '{seq_code}' already exists.")
                continue

            create_obj = SequenceCreate(
                sequence_code=seq_code,
                sequence_name=record.header[:255],
                sequence_type=sequence_type,
                sequence_data=validated_data,
                organization_id=organization_id,
                experiment_id=experiment_id,
                sample_id=sample_id,
            )
            try:
                await sequence_repo.create(
                    db, obj_in=create_obj, tenant_id=tenant_id, current_user_id=current_user.id
                )
                registered += 1
            except Exception as e:
                failed += 1
                errors.append(f"Record '{record.header}': {e}")

        logger.info(f"SequenceService: FASTA upload complete. Registered={registered}, Failed={failed}")
        return FastaUploadResponse(registered=registered, failed=failed, errors=errors)


sequence_service = SequenceService()
