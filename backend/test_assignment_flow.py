import asyncio
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
from app.services.project_service import project_service
from app.services.experiment_service import experiment_service
from app.services.notification_service import notification_service
from app.crud.crud_dashboard import dashboard_repo

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

    projects = await Project.find({"tenant_id": admin.tenant_id}).limit(1).to_list()
    if projects:
        proj = projects[0]
        print(f"Testing assignment of researcher {researcher.username} to project '{proj.name}'...")
        # Add collaborator
        collab = await project_service.add_collaborator(
            project_id=proj.id,
            user_id=researcher.id,
            role="researcher",
            tenant_id=admin.tenant_id,
            current_user=admin
        )
        print("Collaborator added successfully!")

        # Verify notification created
        notifications = await notification_service.get_user_notifications(
            tenant_id=researcher.tenant_id,
            user_id=researcher.id,
            limit=5
        )
        print(f"Researcher latest notification: {notifications[0].title} - {notifications[0].message}")

        # Check dashboard notifications
        dash_notifs = await dashboard_repo.get_pending_notifications(
            tenant_id=researcher.tenant_id,
            user=researcher
        )
        print(f"Dashboard pending notifications count for researcher: {len(dash_notifs)}")
        for dn in dash_notifs:
            print(f" - [{dn.type}] {dn.title}: {dn.message}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
