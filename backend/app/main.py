from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.api.v1.api import api_router
from app.models.tenant import Tenant
from app.models.identity import (
    User, UserProfile, UserRole, UserPreference, RefreshToken,
    UserSession, ApiKey, MFADevice, TrustedDevice, ElectronicSignatureProfile,
    LoginHistory, PasswordHistory
)
from app.models.rbac import Role, Permission, RolePermission

from app.models.project import Project, ProjectCollaborator, ProjectAttachment
from app.models.experiment import Experiment, ExperimentCollaborator, ExperimentAttachment, ExperimentQAComment
from app.models.sample import Sample, SampleType, SampleStorageLocation, SampleChainOfCustody, SampleAttachment, SampleAliquot
from app.models.inventory import InventoryItem, InventoryCategory, InventorySupplier, InventoryLocation, InventoryBatch, InventoryTransaction
from app.models.instrument import Instrument, InstrumentType, InstrumentCalibration, InstrumentMaintenance, InstrumentReservation, InstrumentUsage, InstrumentAttachment
from app.models.sequence import Sequence, SequenceVersion, SequenceAnnotation, SequenceAttachment, SequenceAnalysisResult
from app.models.notebook import NotebookEntry, NotebookEntryVersion, NotebookAttachment, NotebookComment, NotebookTag
from app.models.protocol import Protocol, ProtocolVersion, ProtocolStep, ProtocolAttachment, ProtocolApproval
from app.models.notification import Notification

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Initialize Beanie with our document models
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            Tenant,
            User, UserProfile, UserRole, UserPreference, RefreshToken,
            UserSession, ApiKey, MFADevice, TrustedDevice, ElectronicSignatureProfile,
            LoginHistory, PasswordHistory,
            Role, Permission, RolePermission,
            Project, ProjectCollaborator, ProjectAttachment,
            Experiment, ExperimentCollaborator, ExperimentAttachment, ExperimentQAComment,
            Sample, SampleType, SampleStorageLocation, SampleChainOfCustody, SampleAttachment, SampleAliquot,
            InventoryItem, InventoryCategory, InventorySupplier, InventoryLocation, InventoryBatch, InventoryTransaction,
            Instrument, InstrumentType, InstrumentCalibration, InstrumentMaintenance, InstrumentReservation, InstrumentUsage, InstrumentAttachment,
            Sequence, SequenceVersion, SequenceAnnotation, SequenceAttachment, SequenceAnalysisResult,
            NotebookEntry, NotebookEntryVersion, NotebookAttachment, NotebookComment, NotebookTag,
            Protocol, ProtocolVersion, ProtocolStep, ProtocolAttachment, ProtocolApproval,
            Notification
        ]
    )

    # Auto-seed default admin user according to Sprint PDF Requirement 8
    try:
        from app.db.enums import UserStatus
        from app.services.identity.password_service import password_service
        default_users_data = [
            {"email": "admin@eln.com", "username": "admin", "first": "System", "last": "Admin", "role": "Admin", "dept": "System Administration"},
            {"email": "ashwin.kumar@eln.com", "username": "ashwink", "first": "Dr. Ashwin", "last": "Kumar", "role": "PI", "dept": "Molecular Biology"},
            {"email": "sarah.johnson@eln.com", "username": "sarahj", "first": "Dr. Sarah", "last": "Johnson", "role": "Researcher", "dept": "Gene Editing Discovery"},
            {"email": "raj.patel@eln.com", "username": "rajp", "first": "Raj", "last": "Patel", "role": "Bioinformatician", "dept": "Bioinformatics & RAG"},
            {"email": "ananya.sharma@eln.com", "username": "ananyas", "first": "Ananya", "last": "Sharma", "role": "QA", "dept": "Quality Assurance & Audit"},
            {"email": "viewer@eln.com", "username": "viewer", "first": "Alex", "last": "Taylor", "role": "Viewer", "dept": "External Review & Audit"},
            {"email": "saikiran@eln.com", "username": "saikiran", "first": "Sai", "last": "Kiran", "role": "Admin", "dept": "Infrastructure & DB"},
        ]

        tenant = await Tenant.find_one({"code": "DEFAULT"})
        if not tenant:
            tenant = Tenant(name="Default Tenant", code="DEFAULT")
            await tenant.insert()

        pwd_hash = password_service.hash_password("Admin@12345678")

        for u_data in default_users_data:
            existing = await User.find_one({"email": u_data["email"]})
            if not existing:
                u_obj = User(
                    tenant_id=tenant.id,
                    username=u_data["username"],
                    email=u_data["email"],
                    first_name=u_data["first"],
                    last_name=u_data["last"],
                    display_name=f"{u_data['first']} {u_data['last']}",
                    password_hash=pwd_hash,
                    is_active=True,
                    is_locked=False,
                    status=UserStatus.ACTIVE,
                )
                await u_obj.insert()

                p_obj = UserProfile(
                    user_id=u_obj.id,
                    department=u_data["dept"],
                    designation=u_data["role"],
                )
                await p_obj.insert()

                r_obj = UserRole(
                    user_id=u_obj.id,
                    role_name=u_data["role"],
                    is_primary=True,
                    is_active=True,
                )
                await r_obj.insert()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Admin seeding check warning: {e}")

    yield
    client.close()

app = FastAPI(
    title="Enterprise AI-Powered ELN API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API for the Electronic Laboratory Notebook",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
