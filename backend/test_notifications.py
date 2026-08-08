import asyncio
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.identity import (
    User, UserProfile, UserRole, UserPreference, RefreshToken,
    UserSession, ApiKey, MFADevice, TrustedDevice, ElectronicSignatureProfile,
    LoginHistory, PasswordHistory
)
from app.models.rbac import Role, Permission, RolePermission
from app.models.project import Project, ProjectCollaborator, ProjectAttachment
from app.models.experiment import Experiment, ExperimentCollaborator, ExperimentAttachment
from app.models.sample import Sample, SampleType, SampleStorageLocation, SampleChainOfCustody, SampleAttachment, SampleAliquot
from app.models.inventory import InventoryItem, InventoryCategory, InventorySupplier, InventoryLocation, InventoryBatch, InventoryTransaction
from app.models.instrument import Instrument, InstrumentType, InstrumentCalibration, InstrumentMaintenance, InstrumentReservation, InstrumentUsage, InstrumentAttachment
from app.models.sequence import Sequence, SequenceVersion, SequenceAnnotation, SequenceAttachment, SequenceAnalysisResult
from app.models.notebook import NotebookEntry, NotebookEntryVersion, NotebookAttachment, NotebookComment, NotebookTag
from app.models.protocol import Protocol, ProtocolVersion, ProtocolStep, ProtocolAttachment, ProtocolApproval
from app.models.notification import Notification
from app.services.notification_service import notification_service
from app.services.project_service import project_service

async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            Tenant,
            User, UserProfile, UserRole, UserPreference, RefreshToken,
            UserSession, ApiKey, MFADevice, TrustedDevice, ElectronicSignatureProfile,
            LoginHistory, PasswordHistory,
            Role, Permission, RolePermission,
            Project, ProjectCollaborator, ProjectAttachment,
            Experiment, ExperimentCollaborator, ExperimentAttachment,
            Sample, SampleType, SampleStorageLocation, SampleChainOfCustody, SampleAttachment, SampleAliquot,
            InventoryItem, InventoryCategory, InventorySupplier, InventoryLocation, InventoryBatch, InventoryTransaction,
            Instrument, InstrumentType, InstrumentCalibration, InstrumentMaintenance, InstrumentReservation, InstrumentUsage, InstrumentAttachment,
            Sequence, SequenceVersion, SequenceAnnotation, SequenceAttachment, SequenceAnalysisResult,
            NotebookEntry, NotebookEntryVersion, NotebookAttachment, NotebookComment, NotebookTag,
            Protocol, ProtocolVersion, ProtocolStep, ProtocolAttachment, ProtocolApproval,
            Notification
        ]
    )

    admin = await User.find_one({"username": "ashwink"}) or await User.find_one({"username": "admin"})
    researcher = await User.find_one({"username": "rajmange94_5a81"}) or await User.find_one({"username": "sarahj"})

    print(f"Admin / PI: {admin.username} (ID: {admin.id})")
    print(f"Researcher: {researcher.username} (ID: {researcher.id})")

    # Send a real-time project assignment notification
    n1 = await notification_service.create_notification(
        tenant_id=researcher.tenant_id,
        user_id=researcher.id,
        title="Project Assigned: CRISPR-Cas9 Target Screening",
        message=f"{admin.display_name or admin.username} (PI) assigned you as Lead Researcher on workspace 'CRISPR-Cas9 Target Screening' (PRJ-2026-003).",
        type="assignment",
        entity_type="project",
        sender_id=admin.id,
        sender_name=admin.display_name or admin.username,
    )
    print(f"Created Notification 1: {n1.title}")

    # Send a real-time review request notification
    n2 = await notification_service.create_notification(
        tenant_id=researcher.tenant_id,
        user_id=researcher.id,
        title="Experiment Review Ready: sgRNA Design Batch 1",
        message=f"{admin.display_name or admin.username} requested your peer review on experiment 'sgRNA Design Batch 1' (EXP-2026-104).",
        type="review",
        entity_type="experiment",
        sender_id=admin.id,
        sender_name=admin.display_name or admin.username,
    )
    print(f"Created Notification 2: {n2.title}")

    unread = await notification_service.get_unread_count(tenant_id=researcher.tenant_id, user_id=researcher.id)
    print(f"Unread notifications for {researcher.username}: {unread}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
