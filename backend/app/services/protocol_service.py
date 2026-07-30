import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_protocol import protocol_repo
from app.models.identity import User
from app.models.protocol import (
    Protocol,
    ProtocolApproval,
    ProtocolAttachment,
    ProtocolStep,
    ProtocolVersion,
)
from app.schemas.protocol import (
    ProtocolApprovalCreate,
    ProtocolCreate,
    ProtocolFilter,
    ProtocolPagination,
    ProtocolStepCreate,
    ProtocolUpdate,
)

logger = logging.getLogger(__name__)


# Domain Exceptions
class ProtocolNotFound(Exception):
    pass


class DuplicateProtocolCode(Exception):
    pass


class ProtocolApprovedImmutableError(Exception):
    pass


class InvalidProtocolStepOrder(Exception):
    pass


class UnapprovedProtocolLinkError(Exception):
    pass


class ProtocolService:
    """Service layer enforcing SOP protocol management rules, approval workflows, and version immutability."""

    async def create_protocol(
        self, db: AsyncSession, *, obj_in: ProtocolCreate, tenant_id: UUID, current_user: User
    ) -> Protocol:
        """Create a new protocol SOP ensuring protocol_code is unique per tenant."""
        # 1. Validate Code Uniqueness per Tenant
        existing = await protocol_repo.get_by_code(db, protocol_code=obj_in.protocol_code, tenant_id=tenant_id)
        if existing:
            raise DuplicateProtocolCode(
                f"Protocol code '{obj_in.protocol_code}' already exists in this tenant workspace."
            )

        # 2. Validate Step Number Order
        for step in obj_in.steps:
            if step.step_number <= 0:
                raise InvalidProtocolStepOrder("Step number must be a positive integer greater than 0.")

        protocol = await protocol_repo.create(
            db, obj_in=obj_in, tenant_id=tenant_id, current_user_id=current_user.id
        )
        logger.info(f"ProtocolService: Created protocol '{protocol.protocol_code}' (ID: {protocol.id})")
        return protocol

    async def get_protocol(
        self, db: AsyncSession, *, protocol_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Protocol:
        """Fetch protocol by ID or raise ProtocolNotFound."""
        protocol = await protocol_repo.get_by_id(
            db, id=protocol_id, tenant_id=tenant_id, include_details=include_details
        )
        if not protocol:
            raise ProtocolNotFound(f"Protocol {protocol_id} not found.")
        return protocol

    async def update_protocol(
        self,
        db: AsyncSession,
        *,
        protocol_id: UUID,
        obj_in: ProtocolUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Tuple[Protocol, ProtocolVersion]:
        """Update protocol details. If already approved, increment version number and create a new version snapshot."""
        protocol = await self.get_protocol(db, protocol_id=protocol_id, tenant_id=tenant_id)

        # If protocol was approved, reset status back to 'in_review' or 'draft' when updated
        if protocol.status == "approved":
            protocol.status = "in_review"

        updated_protocol, new_version = await protocol_repo.update(
            db, db_obj=protocol, obj_in=obj_in, current_user_id=current_user.id
        )
        logger.info(f"ProtocolService: Updated protocol {protocol_id} to version {new_version.version_number}")
        return updated_protocol, new_version

    async def add_step(
        self,
        db: AsyncSession,
        *,
        protocol_id: UUID,
        step_in: ProtocolStepCreate,
        tenant_id: UUID,
        current_user: User
    ) -> ProtocolStep:
        """Add a step to an existing protocol."""
        if step_in.step_number <= 0:
            raise InvalidProtocolStepOrder("Step number must be positive.")

        await self.get_protocol(db, protocol_id=protocol_id, tenant_id=tenant_id)
        return await protocol_repo.add_step(db, protocol_id=protocol_id, step_in=step_in)

    async def approve_protocol(
        self,
        db: AsyncSession,
        *,
        protocol_id: UUID,
        obj_in: ProtocolApprovalCreate,
        tenant_id: UUID,
        current_user: User
    ) -> ProtocolApproval:
        """Record an approval or rejection decision for a protocol."""
        protocol = await self.get_protocol(db, protocol_id=protocol_id, tenant_id=tenant_id)

        if obj_in.status.lower() == "approved":
            protocol.status = "approved"
            protocol.approval_date = datetime.now(timezone.utc)
            protocol.reviewer_id = current_user.id
        elif obj_in.status.lower() == "rejected":
            protocol.status = "rejected"

        db.add(protocol)
        await db.commit()

        approval = await protocol_repo.add_approval(
            db,
            protocol_id=protocol_id,
            approver_id=current_user.id,
            status=obj_in.status.lower(),
            comments=obj_in.comments,
        )
        logger.info(f"ProtocolService: Protocol {protocol_id} marked as {protocol.status} by user {current_user.id}")
        return approval

    async def list_protocols(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        filter_params: ProtocolFilter,
        pagination: ProtocolPagination
    ) -> Tuple[List[Protocol], int]:
        """List protocols with filtering and pagination."""
        return await protocol_repo.list_protocols(
            db, tenant_id=tenant_id, filter_params=filter_params, pagination=pagination
        )

    async def list_versions(
        self, db: AsyncSession, *, protocol_id: UUID, tenant_id: UUID
    ) -> List[ProtocolVersion]:
        """Fetch all historical version snapshots for a protocol."""
        await self.get_protocol(db, protocol_id=protocol_id, tenant_id=tenant_id, include_details=False)
        return await protocol_repo.list_versions(db, protocol_id=protocol_id)


protocol_service = ProtocolService()
