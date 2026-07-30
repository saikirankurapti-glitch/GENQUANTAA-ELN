import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.protocol import (
    Protocol,
    ProtocolApproval,
    ProtocolAttachment,
    ProtocolStep,
    ProtocolVersion,
)
from app.schemas.protocol import (
    ProtocolCreate,
    ProtocolFilter,
    ProtocolPagination,
    ProtocolStepCreate,
    ProtocolUpdate,
)

logger = logging.getLogger(__name__)


class ProtocolRepository:
    """Async Repository handling data access for Protocol SOP entities with tenant isolation."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ProtocolCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Protocol:
        """Create a new Protocol, its steps sequence, and initial Version 1 snapshot."""
        protocol = Protocol(
            tenant_id=tenant_id,
            organization_id=obj_in.organization_id,
            protocol_code=obj_in.protocol_code,
            title=obj_in.title,
            description=obj_in.description,
            category=obj_in.category,
            status=obj_in.status,
            current_version=1,
            owner_id=current_user_id,
            reviewer_id=obj_in.reviewer_id,
            metadata_json=obj_in.metadata_json,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(protocol)
        await db.flush()

        # Add initial steps
        for step_data in obj_in.steps:
            step = ProtocolStep(
                protocol_id=protocol.id,
                step_number=step_data.step_number,
                title=step_data.title,
                instructions=step_data.instructions,
                duration_minutes=step_data.duration_minutes,
                safety_notes=step_data.safety_notes,
            )
            db.add(step)

        # Create Version 1 snapshot
        version_1 = ProtocolVersion(
            protocol_id=protocol.id,
            version_number=1,
            content_snapshot={
                "title": obj_in.title,
                "description": obj_in.description,
                "category": obj_in.category,
                "steps": [s.model_dump() for s in obj_in.steps],
            },
            change_reason="Initial protocol registration.",
            created_by=current_user_id,
        )
        db.add(version_1)

        await db.commit()
        await db.refresh(protocol)
        return protocol

    async def get_by_id(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Protocol]:
        """Fetch Protocol by ID within tenant scope."""
        stmt = select(Protocol).where(
            Protocol.id == id,
            Protocol.tenant_id == tenant_id,
            Protocol.is_deleted == False
        )
        if include_details:
            stmt = stmt.options(
                selectinload(Protocol.steps),
                selectinload(Protocol.versions),
                selectinload(Protocol.attachments),
                selectinload(Protocol.approvals),
                selectinload(Protocol.owner),
                selectinload(Protocol.reviewer),
            )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(
        self, db: AsyncSession, *, protocol_code: str, tenant_id: UUID
    ) -> Optional[Protocol]:
        """Fetch Protocol by code within tenant scope."""
        stmt = select(Protocol).where(
            Protocol.protocol_code == protocol_code.upper(),
            Protocol.tenant_id == tenant_id,
            Protocol.is_deleted == False
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Protocol,
        obj_in: ProtocolUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[Protocol, ProtocolVersion]:
        """Update Protocol attributes, increment version number and create a new ProtocolVersion snapshot."""
        new_version_number = db_obj.current_version + 1
        db_obj.current_version = new_version_number

        if obj_in.title is not None:
            db_obj.title = obj_in.title
        if obj_in.description is not None:
            db_obj.description = obj_in.description
        if obj_in.category is not None:
            db_obj.category = obj_in.category
        if obj_in.reviewer_id is not None:
            db_obj.reviewer_id = obj_in.reviewer_id

        db_obj.updated_by = current_user_id
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)

        version_snapshot = ProtocolVersion(
            protocol_id=db_obj.id,
            version_number=new_version_number,
            content_snapshot={
                "title": db_obj.title,
                "description": db_obj.description,
                "category": db_obj.category,
            },
            change_reason=obj_in.change_reason or f"Updated to version {new_version_number}",
            created_by=current_user_id,
        )
        db.add(version_snapshot)

        await db.commit()
        await db.refresh(db_obj)
        await db.refresh(version_snapshot)
        return db_obj, version_snapshot

    async def archive(
        self, db: AsyncSession, *, protocol_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Protocol]:
        """Archive a Protocol."""
        protocol = await self.get_by_id(db, id=protocol_id, tenant_id=tenant_id)
        if not protocol:
            return None

        protocol.status = "archived"
        protocol.archived_at = datetime.now(timezone.utc)
        protocol.updated_by = current_user_id
        db.add(protocol)
        await db.commit()
        await db.refresh(protocol)
        return protocol

    async def restore(
        self, db: AsyncSession, *, protocol_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Protocol]:
        """Restore an archived Protocol."""
        protocol = await self.get_by_id(db, id=protocol_id, tenant_id=tenant_id)
        if not protocol:
            return None

        protocol.status = "draft"
        protocol.archived_at = None
        protocol.updated_by = current_user_id
        db.add(protocol)
        await db.commit()
        await db.refresh(protocol)
        return protocol

    async def soft_delete(
        self, db: AsyncSession, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft delete Protocol."""
        protocol = await self.get_by_id(db, id=id, tenant_id=tenant_id)
        if not protocol:
            return False

        protocol.is_deleted = True
        protocol.deleted_at = datetime.now(timezone.utc)
        protocol.deleted_by = current_user_id
        db.add(protocol)
        await db.commit()
        return True

    async def list_protocols(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: ProtocolFilter,
        pagination: ProtocolPagination
    ) -> Tuple[List[Protocol], int]:
        """List and search Protocols with filtering and pagination."""
        query = select(Protocol).where(
            Protocol.tenant_id == tenant_id,
            Protocol.is_deleted == False
        )

        if filter_params.category:
            query = query.where(Protocol.category == filter_params.category)
        if filter_params.status:
            query = query.where(Protocol.status == filter_params.status)
        if filter_params.owner_id:
            query = query.where(Protocol.owner_id == filter_params.owner_id)
        if filter_params.search:
            pattern = f"%{filter_params.search}%"
            query = query.where(
                or_(
                    Protocol.protocol_code.ilike(pattern),
                    Protocol.title.ilike(pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Sorting & Pagination
        sort_col = getattr(Protocol, pagination.sort_by, Protocol.created_at)
        if pagination.sort_order.lower() == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        res = await db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def list_versions(
        self, db: AsyncSession, *, protocol_id: UUID
    ) -> List[ProtocolVersion]:
        """Fetch all historical version snapshots for a protocol."""
        stmt = (
            select(ProtocolVersion)
            .where(ProtocolVersion.protocol_id == protocol_id)
            .order_by(ProtocolVersion.version_number.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_step(
        self, db: AsyncSession, *, protocol_id: UUID, step_in: ProtocolStepCreate
    ) -> ProtocolStep:
        """Add a step to a Protocol."""
        step = ProtocolStep(
            protocol_id=protocol_id,
            step_number=step_in.step_number,
            title=step_in.title,
            instructions=step_in.instructions,
            duration_minutes=step_in.duration_minutes,
            safety_notes=step_in.safety_notes,
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)
        return step

    async def add_attachment(
        self,
        db: AsyncSession,
        *,
        protocol_id: UUID,
        filename: str,
        blob_path: str,
        mime_type: Optional[str],
        file_size: int,
        checksum: str,
        current_user_id: Optional[UUID] = None
    ) -> ProtocolAttachment:
        """Add an attachment to a Protocol."""
        attachment = ProtocolAttachment(
            protocol_id=protocol_id,
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

    async def add_approval(
        self,
        db: AsyncSession,
        *,
        protocol_id: UUID,
        approver_id: UUID,
        status: str,
        comments: Optional[str] = None
    ) -> ProtocolApproval:
        """Record an approval decision for a Protocol."""
        approval = ProtocolApproval(
            protocol_id=protocol_id,
            approver_id=approver_id,
            status=status,
            comments=comments,
        )
        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        return approval


protocol_repo = ProtocolRepository()
