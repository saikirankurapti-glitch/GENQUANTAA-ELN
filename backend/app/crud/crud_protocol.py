import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Any
from uuid import UUID, uuid4

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
        *,
        obj_in: ProtocolCreate,
        tenant_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Protocol:
        """Create a new Protocol, its steps sequence, and initial Version 1 snapshot."""
        protocol = Protocol(
            tenant_id=tenant_id,
            author_id=current_user_id,
            protocol_code=obj_in.protocol_code,
            title=obj_in.title,
            description=obj_in.description,
            category=obj_in.category,
            status=obj_in.status,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await protocol.insert()

        # Add initial steps
        for step_data in obj_in.steps:
            step = ProtocolStep(
                protocol_id=protocol.id,
                step_order=step_data.step_number,
                title=step_data.title,
                instructions=step_data.instructions,
            )
            await step.insert()

        # Create Version 1 snapshot
        version_1 = ProtocolVersion(
            protocol_id=protocol.id,
            version=1,
            title=obj_in.title,
            content=obj_in.description,
        )
        await version_1.insert()

        return protocol

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, include_details: bool = False
    ) -> Optional[Protocol]:
        """Fetch Protocol by ID within tenant scope."""
        protocol = await Protocol.find_one(
            Protocol.id == id,
            Protocol.tenant_id == tenant_id,
            Protocol.is_deleted == False
        )
        return protocol

    async def get_by_code(
        self, *, protocol_code: str, tenant_id: UUID
    ) -> Optional[Protocol]:
        """Fetch Protocol by code within tenant scope."""
        protocol = await Protocol.find_one(
            Protocol.protocol_code == protocol_code.upper(),
            Protocol.tenant_id == tenant_id,
            Protocol.is_deleted == False
        )
        return protocol

    async def update(
        self,
        *,
        db_obj: Protocol,
        obj_in: ProtocolUpdate,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[Protocol, ProtocolVersion]:
        """Update Protocol attributes."""
        # Find current version to increment
        latest_version = await ProtocolVersion.find(ProtocolVersion.protocol_id == db_obj.id).sort(-ProtocolVersion.version).first_or_none()
        new_version_number = (latest_version.version + 1) if latest_version else 1

        if obj_in.title is not None:
            db_obj.title = obj_in.title
        if obj_in.description is not None:
            db_obj.description = obj_in.description
        if obj_in.category is not None:
            db_obj.category = obj_in.category

        db_obj.updated_at = datetime.now(timezone.utc)
        await db_obj.save()

        version_snapshot = ProtocolVersion(
            protocol_id=db_obj.id,
            version=new_version_number,
            title=db_obj.title,
            content=db_obj.description,
        )
        await version_snapshot.insert()

        return db_obj, version_snapshot

    async def archive(
        self, *, protocol_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Protocol]:
        """Archive a Protocol."""
        protocol = await self.get_by_id(id=protocol_id, tenant_id=tenant_id)
        if not protocol:
            return None

        protocol.status = "archived"
        protocol.updated_at = datetime.now(timezone.utc)
        await protocol.save()
        return protocol

    async def restore(
        self, *, protocol_id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> Optional[Protocol]:
        """Restore an archived Protocol."""
        protocol = await self.get_by_id(id=protocol_id, tenant_id=tenant_id)
        if not protocol:
            return None

        protocol.status = "active"
        protocol.updated_at = datetime.now(timezone.utc)
        await protocol.save()
        return protocol

    async def soft_delete(
        self, *, id: UUID, tenant_id: UUID, current_user_id: Optional[UUID] = None
    ) -> bool:
        """Soft delete Protocol."""
        protocol = await self.get_by_id(id=id, tenant_id=tenant_id)
        if not protocol:
            return False

        protocol.is_deleted = True
        protocol.updated_at = datetime.now(timezone.utc)
        await protocol.save()
        return True

    async def list_protocols(
        self,
        *,
        tenant_id: UUID,
        filter_params: ProtocolFilter,
        pagination: ProtocolPagination
    ) -> Tuple[List[dict], int]:
        """List and search Protocols with filtering and pagination."""
        query = Protocol.find(
            Protocol.tenant_id == tenant_id,
            Protocol.is_deleted == False
        )

        if filter_params.category:
            query = query.find(Protocol.category == filter_params.category)
        if filter_params.status:
            query = query.find(Protocol.status == filter_params.status)
        if filter_params.owner_id:
            query = query.find(Protocol.author_id == filter_params.owner_id)
        if filter_params.search:
            query = query.find({"$or": [
                {"protocol_code": {"$regex": filter_params.search, "$options": "i"}},
                {"title": {"$regex": filter_params.search, "$options": "i"}},
            ]})

        total = await query.count()
        skip = (pagination.page - 1) * pagination.page_size
        items = await query.sort(-Protocol.created_at).skip(skip).limit(pagination.page_size).to_list()
        
        mapped_items = []
        for i in items:
            latest_v = await ProtocolVersion.find(ProtocolVersion.protocol_id == i.id).sort(-ProtocolVersion.version).first_or_none()
            mapped_items.append({
                "id": i.id,
                "tenant_id": i.tenant_id,
                "organization_id": i.tenant_id,
                "protocol_code": i.protocol_code,
                "title": i.title,
                "description": i.description,
                "category": i.category,
                "status": i.status,
                "current_version": latest_v.version if latest_v else 1,
                "owner_id": i.author_id,
                "reviewer_id": None,
                "approval_date": None,
                "created_at": i.created_at,
                "updated_at": i.updated_at
            })

        return mapped_items, total

    async def list_versions(
        self, *, protocol_id: UUID
    ) -> List[ProtocolVersion]:
        """Fetch all historical version snapshots for a protocol."""
        return await ProtocolVersion.find(ProtocolVersion.protocol_id == protocol_id).sort(-ProtocolVersion.version).to_list()

    async def add_step(
        self, *, protocol_id: UUID, step_in: ProtocolStepCreate
    ) -> ProtocolStep:
        """Add a step to a Protocol."""
        step = ProtocolStep(
            protocol_id=protocol_id,
            step_order=step_in.step_number,
            title=step_in.title,
            instructions=step_in.instructions,
        )
        await step.insert()
        return step

    async def add_attachment(
        self,
        *,
        protocol_id: UUID,
        filename: str,
        blob_path: str,
        mime_type: Optional[str],
        file_size: int,
        checksum: str,
        current_user_id: Optional[UUID] = None
    ) -> ProtocolAttachment:
        """Link an uploaded file attachment to the protocol."""
        attachment = ProtocolAttachment(
            protocol_id=protocol_id,
            file_name=filename,
            file_path=blob_path,
        )
        await attachment.insert()
        return attachment

    async def get_attachments(
        self, *, protocol_id: UUID
    ) -> List[ProtocolAttachment]:
        """Get attachments for a protocol."""
        return await ProtocolAttachment.find(ProtocolAttachment.protocol_id == protocol_id).to_list()

    async def add_approval(
        self,
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
        await approval.insert()
        return approval


protocol_repo = ProtocolRepository()
