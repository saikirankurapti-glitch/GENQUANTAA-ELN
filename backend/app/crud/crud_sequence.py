import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

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
    """Async Repository for Sequence entities with strict tenant isolation (Beanie version)."""

    async def create(
        self,
        *,
        obj_in: SequenceCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None,
    ) -> Sequence:
        """Create a new Sequence record and snapshot the first version."""
        seq_data = obj_in.sequence_data.upper()
        # Clean sequence for pitch demo to prevent crashes
        from app.utils.bioinformatics import clean_sequence, calculate_gc_content, calculate_molecular_weight
        clean_seq = clean_sequence(seq_data)
        
        length = len(clean_seq)
        gc = calculate_gc_content(clean_seq)
        mw = calculate_molecular_weight(clean_seq, obj_in.sequence_type)

        seq = Sequence(
            tenant_id=tenant_id,
            experiment_id=obj_in.experiment_id,
            sample_id=obj_in.sample_id,
            name=obj_in.sequence_name,
            sequence_type=obj_in.sequence_type,
            sequence_data=clean_seq,  # save cleaned data
            length=length,
            status="active",
            gc_content=gc,
            molecular_weight=mw,
            is_deleted=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await seq.insert()

        # Snapshot version 1
        sv = SequenceVersion(
            sequence_id=seq.id,
            version=1,
            sequence_data=seq_data,
            created_at=datetime.now(timezone.utc)
        )
        await sv.insert()

        return seq

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Sequence]:
        """Fetch Sequence by ID."""
        return await Sequence.find_one(
            Sequence.id == id,
            Sequence.tenant_id == tenant_id,
            Sequence.is_deleted == False
        )

    async def update(
        self,
        *,
        db_obj: Sequence,
        obj_in: SequenceUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Sequence:
        """Update existing Sequence attributes. Records new version if sequence_data changes."""
        update_data = obj_in.model_dump(exclude_unset=True)
        new_version_needed = False

        if "sequence_data" in update_data and update_data["sequence_data"]:
            from app.utils.bioinformatics import clean_sequence, calculate_gc_content, calculate_molecular_weight
            new_data = clean_sequence(update_data["sequence_data"])
            seq_type = update_data.get("sequence_type", db_obj.sequence_type)
            
            if new_data != db_obj.sequence_data:
                db_obj.sequence_data = new_data
                db_obj.length = len(new_data)
                db_obj.gc_content = calculate_gc_content(new_data)
                db_obj.molecular_weight = calculate_molecular_weight(new_data, seq_type)
                new_version_needed = True

        if "sequence_name" in update_data:
            db_obj.name = update_data["sequence_name"]
            
        if "sequence_type" in update_data:
            db_obj.sequence_type = update_data["sequence_type"]

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()

        if new_version_needed:
            # We don't track the exact integer version on the Sequence model in Beanie right now, so we just count existing versions
            count = await SequenceVersion.find({"sequence_id": db_obj.id}).count()
            sv = SequenceVersion(
                sequence_id=db_obj.id,
                version=count + 1,
                sequence_data=db_obj.sequence_data,
                created_at=datetime.now(timezone.utc)
            )
            await sv.insert()

        return db_obj

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        seq = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not seq:
            return False
        seq.is_deleted = True
        seq.updated_at = datetime.now(timezone.utc)
        await seq.save()
        return True

    async def get_multi(
        self,
        *,
        tenant_id: UUID,
        sequence_type: Optional[str] = None,
        status: Optional[str] = None,
        experiment_id: Optional[UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        query = Sequence.find(
            Sequence.tenant_id == tenant_id,
            Sequence.is_deleted == False
        )

        if sequence_type:
            query = query.find(Sequence.sequence_type == sequence_type)
        if status:
            query = query.find(Sequence.status == status)
        if experiment_id:
            query = query.find(Sequence.experiment_id == experiment_id)

        if search:
            query = query.find({"$or": [
                {"name": {"$regex": search, "$options": "i"}},
            ]})

        total = await query.count()
        items = await query.sort(-Sequence.created_at).skip(skip).limit(limit).to_list()
        
        mapped_items = []
        for i in items:
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": tenant_id,
                "experiment_id": i.experiment_id,
                "sample_id": i.sample_id,
                "sequence_code": f"SEQ-{str(i.id).split('-')[0].upper()}",
                "sequence_name": i.name,
                "sequence_type": "RNA" if i.sequence_type.upper() == "MRNA" else ("DNA" if i.sequence_type.upper() not in ["DNA", "RNA", "PROTEIN"] else i.sequence_type.upper()),
                "source": "Unknown",
                "molecular_weight": getattr(i, 'molecular_weight', 0.0),
                "sequence_data": i.sequence_data,
                "length": i.length,
                "gc_content": i.gc_content,
                "status": i.status,
                "version": 1,
                "metadata_json": {},
                "created_at": i.created_at,
                "updated_at": i.updated_at
            })

        return mapped_items, total

sequence_repo = SequenceRepository()
