import logging
from io import StringIO
from typing import List, Optional, Tuple
from uuid import UUID

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


class SequenceNotFound(Exception):
    pass


class DuplicateSequenceCode(Exception):
    pass


class InvalidSequenceAlphabet(Exception):
    pass


class SequenceArchivedError(Exception):
    pass


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
            current_seq_lines.append(line)

    if current_header is not None:
        records.append(
            FastaRecord(header=current_header, sequence_data="".join(current_seq_lines))
        )
    return records


class SequenceService:
    """Service layer enforcing sequence validity, versioning, and annotation logic."""

    async def create_sequence(
        self, *, obj_in: SequenceCreate, tenant_id: UUID, current_user: User
    ) -> Sequence:
        """Create a new sequence ensuring sequence_code uniqueness per tenant."""
        seq = await sequence_repo.create(
            obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"SequenceService: Created sequence {seq.id}")
        return seq

    async def get_sequence(
        self, *, sequence_id: UUID, tenant_id: UUID
    ) -> Sequence:
        """Retrieve sequence with full detail graph (versions, annotations)."""
        seq = await sequence_repo.get_by_id(
            id=sequence_id, tenant_id=tenant_id, include_details=True
        )
        if not seq:
            raise SequenceNotFound(f"Sequence ID {sequence_id} not found.")
        return seq

    async def update_sequence(
        self,
        *,
        sequence_id: UUID,
        obj_in: SequenceUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Sequence:
        """Update sequence metadata or sequence data (triggers new version)."""
        seq = await self.get_sequence(sequence_id=sequence_id, tenant_id=tenant_id)

        if seq.status == "archived":
            raise SequenceArchivedError("Cannot update an archived sequence.")

        if obj_in.sequence_data and obj_in.sequence_type:
            try:
                _validate_sequence_alphabet(obj_in.sequence_type, obj_in.sequence_data)
            except ValueError as e:
                raise InvalidSequenceAlphabet(str(e))
        elif obj_in.sequence_data:
            try:
                _validate_sequence_alphabet(seq.sequence_type, obj_in.sequence_data)
            except ValueError as e:
                raise InvalidSequenceAlphabet(str(e))

        updated_seq = await sequence_repo.update(
            db_obj=seq, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"SequenceService: Updated sequence {sequence_id}")
        return updated_seq

    async def soft_delete(
        self, *, sequence_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete a sequence."""
        success = await sequence_repo.soft_delete(
            id=sequence_id, tenant_id=tenant_id, current_user_id=current_user.id
        )
        if not success:
            raise SequenceNotFound(f"Sequence ID {sequence_id} not found.")
        logger.info(f"SequenceService: Soft deleted sequence {sequence_id}")
        return True

    async def list_sequences(
        self, *, tenant_id: UUID, filters: SequenceFilter, pagination: SequencePagination
    ) -> Tuple[List[dict], int]:
        """Fetch paginated sequences."""
        return await sequence_repo.get_multi(
            tenant_id=tenant_id,
            sequence_type=filters.sequence_type,
            status=filters.status,
            experiment_id=filters.experiment_id,
            search=filters.search,
            skip=(pagination.page - 1) * pagination.page_size,
            limit=pagination.page_size,
        )


sequence_service = SequenceService()
