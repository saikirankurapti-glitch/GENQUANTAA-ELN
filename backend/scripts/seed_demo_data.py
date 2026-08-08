"""
=====================================================================
  GENQUANTAA ELN - Demo Data Seed Script
  Populates all major modules with realistic life-science data.

  Run from the backend directory with the venv active:
      python scripts/seed_demo_data.py

  Modules seeded:
    - Projects
    - Experiments
    - Protocol Management
    - ELN Editor (Notebook Entries)
    - Sample Registry
    - Inventory Management
    - Instrument Management
    - Sequence Management (+ Viewer data)
=====================================================================
"""

import asyncio
import logging
import sys
import os

# Allow imports from the parent `app` package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.core.config import settings
from app.db.enums import ProjectStatus, ExperimentStatus

# ── Models ─────────────────────────────────────────────────────────────────
from app.models.tenant import Tenant
from app.models.identity import User
from app.models.project import Project, ProjectCollaborator
from app.models.experiment import Experiment, ExperimentCollaborator
from app.models.protocol import Protocol, ProtocolStep, ProtocolVersion, ProtocolApproval
from app.models.notebook import NotebookEntry, NotebookComment, NotebookTag
from app.models.sample import Sample, SampleType, SampleStorageLocation, SampleChainOfCustody
from app.models.inventory import (
    InventoryCategory, InventorySupplier, InventoryLocation,
    InventoryItem, InventoryBatch, InventoryTransaction
)
from app.models.instrument import (
    InstrumentType, Instrument, InstrumentCalibration,
    InstrumentMaintenance, InstrumentReservation
)
from app.models.sequence import (
    Sequence, SequenceAnnotation, SequenceAnalysisResult
)

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

def now(offset_days: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=offset_days)


# =============================================================================
#  INIT BEANIE
# =============================================================================
async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            Tenant, User,
            Project, ProjectCollaborator,
            Experiment, ExperimentCollaborator,
            Protocol, ProtocolStep, ProtocolVersion, ProtocolApproval,
            NotebookEntry, NotebookComment, NotebookTag,
            Sample, SampleType, SampleStorageLocation, SampleChainOfCustody,
            InventoryCategory, InventorySupplier, InventoryLocation,
            InventoryItem, InventoryBatch, InventoryTransaction,
            InstrumentType, Instrument, InstrumentCalibration,
            InstrumentMaintenance, InstrumentReservation,
            Sequence, SequenceAnnotation, SequenceAnalysisResult,
        ]
    )
    return client


# =============================================================================
#  HELPERS
# =============================================================================
async def get_users(tenant_id):
    """Return a dict { role_name: User } for the demo tenant."""
    users = await User.find({"tenant_id": tenant_id}).to_list()
    role_map = {}
    for u in users:
        role_map[u.username] = u
    return role_map


# =============================================================================
#  1. PROJECTS
# =============================================================================
PROJECTS_DATA = [
    {
        "name": "CRISPR-Cas9 Gene Editing – VEGFR2 Target",
        "project_code": "GQ-PROJ-001",
        "description": (
            "Systematic validation of CRISPR-Cas9 editing efficiency on the VEGFR2 "
            "locus in HEK293T cells. This project aims to optimise sgRNA design, "
            "delivery vectors, and off-target analysis pipelines for a therapeutic "
            "oncology application."
        ),
        "objective": "Achieve ≥80% knock-out efficiency with <0.1% off-target indel rate.",
        "status": ProjectStatus.ACTIVE,
        "priority": "HIGH",
        "tags": ["CRISPR", "gene-editing", "oncology", "VEGFR2"],
        "visibility": "PRIVATE",
    },
    {
        "name": "mRNA Vaccine Candidate Screening – Influenza H3N2",
        "project_code": "GQ-PROJ-002",
        "description": (
            "Pre-clinical screening of five mRNA vaccine candidates targeting the H3N2 "
            "haemagglutinin antigen. The project covers formulation optimisation, "
            "immunogenicity assessment in murine models, and biodistribution studies."
        ),
        "objective": "Select top-2 candidates for Phase-I IND filing by Q4.",
        "status": ProjectStatus.ACTIVE,
        "priority": "HIGH",
        "tags": ["mRNA", "vaccine", "influenza", "immunology"],
        "visibility": "INTERNAL",
    },
    {
        "name": "Next-Generation Sequencing – Microbiome Profiling",
        "project_code": "GQ-PROJ-003",
        "description": (
            "16S rRNA amplicon sequencing of gut microbiome samples from 120 human "
            "subjects enrolled in a controlled dietary intervention trial. Bioinformatics "
            "pipeline uses QIIME2 + custom Python scripts for OTU clustering."
        ),
        "objective": "Identify microbial biomarkers correlated with insulin sensitivity.",
        "status": ProjectStatus.PLANNED,
        "priority": "MEDIUM",
        "tags": ["NGS", "microbiome", "16S", "metabolomics"],
        "visibility": "PRIVATE",
    },
    {
        "name": "Protein Crystallography – BRAF V600E Inhibitor Complex",
        "project_code": "GQ-PROJ-004",
        "description": (
            "X-ray crystallography study of novel small-molecule inhibitors bound to "
            "the BRAF V600E oncogenic kinase. Structures will guide lead optimisation "
            "for a melanoma drug discovery programme."
        ),
        "objective": "Solve ≥3 crystal structures at resolution <2.5 Å.",
        "status": ProjectStatus.ACTIVE,
        "priority": "MEDIUM",
        "tags": ["crystallography", "BRAF", "drug-discovery", "oncology"],
        "visibility": "PRIVATE",
    },
]


async def seed_projects(tenant_id, users):
    pi_user = users.get("ashwink")
    researcher = users.get("sarahj")
    bio_user = users.get("rajp")

    project_ids = []
    for pd in PROJECTS_DATA:
        existing = await Project.find_one({"project_code": pd["project_code"]})
        if existing:
            log.info(f"  ↳ Project already exists: {pd['project_code']}")
            project_ids.append(existing.id)
            continue

        proj = Project(
            tenant_id=tenant_id,
            owner_id=pi_user.id if pi_user else uuid4(),
            name=pd["name"],
            project_code=pd["project_code"],
            description=pd["description"],
            objective=pd["objective"],
            status=pd["status"],
            priority=pd["priority"],
            tags=pd["tags"],
            visibility=pd["visibility"],
            start_date=now(-30),
            target_end_date=now(180),
        )
        await proj.insert()
        log.info(f"  ✓ Project: {proj.project_code}")
        project_ids.append(proj.id)

        # Add collaborators
        members = [
            (researcher, "Researcher"),
            (bio_user, "Bioinformatician"),
        ]
        for user, role in members:
            if user:
                collab = ProjectCollaborator(
                    project_id=proj.id,
                    user_id=user.id,
                    role=role,
                    tenant_id=tenant_id,
                )
                await collab.insert()

    return project_ids


# =============================================================================
#  2. PROTOCOLS
# =============================================================================
PROTOCOLS_DATA = [
    {
        "title": "RNA Extraction – TRIzol Method (SOP-RNA-001)",
        "protocol_code": "SOP-RNA-001",
        "category": "extraction",
        "description": (
            "Standard operating procedure for total RNA extraction from cultured "
            "mammalian cells using TRIzol reagent followed by column purification. "
            "Yields typically 5–20 µg of high-quality RNA (RIN ≥ 8.5)."
        ),
        "steps": [
            ("Reagent Preparation", "Prepare TRIzol reagent (1 mL per 10⁶ cells). Warm all solutions to room temperature (25°C). Label all tubes."),
            ("Cell Lysis", "Remove culture media. Add 1 mL TRIzol directly to adherent cells. Pipette vigorously to lyse. Incubate 5 min at RT."),
            ("Phase Separation", "Add 0.2 mL chloroform per mL TRIzol. Shake vigorously 15 s. Incubate 2–3 min at RT. Centrifuge 12,000 × g, 4°C, 15 min."),
            ("RNA Precipitation", "Transfer aqueous phase to fresh tube. Add 0.5 mL isopropanol. Mix. Incubate 10 min at RT. Centrifuge 12,000 × g, 4°C, 10 min."),
            ("Washing", "Discard supernatant. Add 1 mL 75% ethanol. Vortex 15 s. Centrifuge 7,500 × g, 4°C, 5 min. Decant ethanol carefully."),
            ("Resuspension & QC", "Air-dry pellet 5–10 min (avoid over-drying). Resuspend in 30–50 µL RNase-free water. Measure A260/A280 on NanoDrop. Store at -80°C."),
        ],
    },
    {
        "title": "PCR Amplification – Standard Taq Protocol (SOP-PCR-002)",
        "protocol_code": "SOP-PCR-002",
        "category": "amplification",
        "description": (
            "Routine PCR amplification for fragments up to 3 kb using Taq DNA "
            "Polymerase. Suitable for genotyping, colony screening, and fragment "
            "preparation prior to gel purification."
        ),
        "steps": [
            ("Master Mix Preparation", "On ice: mix 25 µL 2× Taq Master Mix + 1 µL Forward Primer (10 µM) + 1 µL Reverse Primer (10 µM) + 2 µL gDNA template + 21 µL nuclease-free water. Vortex gently."),
            ("Thermocycler Settings", "Initial denaturation 95°C 3 min → 35 cycles (95°C 30 s → 58°C 30 s → 72°C 1 min/kb) → Final extension 72°C 5 min → Hold 4°C."),
            ("Gel Electrophoresis", "Run 5 µL PCR product on 1.5% agarose gel (TAE, 100 V, 30 min) with 1 kb DNA ladder. Visualise on UV transilluminator."),
            ("Band Excision & Purification", "Excise band. Purify using gel extraction kit per manufacturer protocol. Elute in 30 µL EB buffer. Quantify on NanoDrop."),
        ],
    },
    {
        "title": "ELISA – Sandwich Format Cytokine Quantification (SOP-ELISA-003)",
        "protocol_code": "SOP-ELISA-003",
        "category": "assay",
        "description": (
            "Sandwich ELISA for quantification of secreted cytokines (IL-6, TNF-α, "
            "IFN-γ) in cell culture supernatants and serum samples. Sensitivity "
            "range: 4–500 pg/mL."
        ),
        "steps": [
            ("Plate Coating", "Coat 96-well plate with 100 µL/well capture antibody (1 µg/mL in PBS). Seal. Incubate overnight at 4°C."),
            ("Blocking", "Wash 3× with PBST. Block with 200 µL/well 1% BSA in PBS for 1 hr at RT. Wash 3× with PBST."),
            ("Sample Incubation", "Add 100 µL/well of standards and samples (diluted in sample diluent). Seal. Incubate 2 hr at RT on shaker."),
            ("Detection Antibody", "Wash 3× PBST. Add 100 µL/well detection antibody (0.5 µg/mL). Incubate 1 hr RT."),
            ("Enzyme Conjugate", "Wash 3× PBST. Add 100 µL/well streptavidin-HRP (1:1000). Incubate 30 min RT."),
            ("Colour Development & Reading", "Wash 5× PBST. Add 100 µL TMB substrate. Incubate 15 min dark. Stop with 50 µL 2N H₂SO₄. Read A450 on plate reader within 30 min."),
        ],
    },
    {
        "title": "Western Blot – Standard SDS-PAGE Protocol (SOP-WB-004)",
        "protocol_code": "SOP-WB-004",
        "category": "protein-analysis",
        "description": (
            "Denaturing SDS-PAGE followed by wet transfer to PVDF membrane for "
            "immunodetection of target proteins. Compatible with cell lysates, "
            "tissue homogenates, and immunoprecipitated samples."
        ),
        "steps": [
            ("Sample Preparation", "Lyse cells in RIPA buffer + protease inhibitors. BCA protein quantification. Load 20–40 µg per lane in Laemmli buffer. Boil 5 min."),
            ("SDS-PAGE", "Cast 10% or 12% polyacrylamide gel. Load samples alongside molecular weight ladder. Run at 80 V (stacking) then 120 V (resolving) for ~90 min."),
            ("Transfer", "Wet transfer to PVDF membrane (pre-activated in methanol) at 100 V, 1 hr, 4°C in transfer buffer. Ponceau S stain to verify transfer efficiency."),
            ("Blocking & Primary Antibody", "Block in 5% non-fat milk/TBST for 1 hr RT. Incubate primary antibody overnight 4°C (dilution per datasheet). Wash 3× TBST."),
            ("Secondary Antibody & Detection", "Incubate HRP-conjugated secondary Ab 1 hr RT. Wash 3× TBST. Apply ECL substrate. Expose to X-ray film or chemiluminescence imager."),
        ],
    },
    {
        "title": "Flow Cytometry – Cell Surface Immunophenotyping (SOP-FLOW-005)",
        "protocol_code": "SOP-FLOW-005",
        "category": "cytometry",
        "description": (
            "Multi-colour flow cytometry panel for immunophenotyping of lymphocyte "
            "subsets (CD3, CD4, CD8, CD19, NK cells) from PBMCs. Maximum 8-colour "
            "panel on BD LSRFortessa."
        ),
        "steps": [
            ("PBMC Isolation", "Dilute blood 1:1 PBS. Layer over Ficoll-Paque. Centrifuge 400 × g 30 min no brake. Collect buffy coat. Wash 2× PBS."),
            ("Fc Block", "Resuspend 10⁶ cells in 100 µL FACS buffer. Add Fc block (10 µg/mL). Incubate 10 min 4°C."),
            ("Antibody Staining", "Add antibody cocktail per panel design (titrated concentrations). Incubate 30 min 4°C dark. Wash 2× FACS buffer."),
            ("Viability Stain", "Resuspend in 100 µL PBS. Add viability dye 1:1000. Incubate 15 min RT dark. Wash 1× FACS buffer."),
            ("Acquisition", "Resuspend in 300 µL FACS buffer. Acquire on LSRFortessa: collect ≥50,000 live singlet events. Export .fcs files."),
            ("Analysis", "Import .fcs into FlowJo. Apply sequential gating: singlets → live → lymphocytes → CD3+ → CD4/CD8 split. Export statistics to CSV."),
        ],
    },
]


async def seed_protocols(tenant_id, users, project_ids):
    pi_user = users.get("ashwink")
    qa_user = users.get("ananyas")
    protocol_ids = []

    for i, pd in enumerate(PROTOCOLS_DATA):
        existing = await Protocol.find_one({"protocol_code": pd["protocol_code"]})
        if existing:
            log.info(f"  ↳ Protocol already exists: {pd['protocol_code']}")
            protocol_ids.append(existing.id)
            continue

        proto = Protocol(
            tenant_id=tenant_id,
            author_id=pi_user.id if pi_user else uuid4(),
            title=pd["title"],
            protocol_code=pd["protocol_code"],
            category=pd["category"],
            description=pd["description"],
            status="active",
        )
        await proto.insert()
        log.info(f"  ✓ Protocol: {proto.protocol_code}")
        protocol_ids.append(proto.id)

        # Protocol Steps
        for step_order, (title, instructions) in enumerate(pd["steps"], start=1):
            step = ProtocolStep(
                protocol_id=proto.id,
                step_order=step_order,
                title=title,
                instructions=instructions,
            )
            await step.insert()

        # Protocol Version snapshot
        version = ProtocolVersion(
            protocol_id=proto.id,
            version=1,
            title=pd["title"],
            content=pd["description"],
        )
        await version.insert()

        # QA Approval record
        if qa_user:
            approval = ProtocolApproval(
                protocol_id=proto.id,
                approver_id=qa_user.id,
                status="approved" if i < 3 else "pending",
            )
            await approval.insert()

    return protocol_ids


# =============================================================================
#  3. EXPERIMENTS & ELN NOTEBOOK ENTRIES
# =============================================================================
EXPERIMENTS_DATA = [
    {
        "title": "sgRNA Design & Efficiency Screening – Round 1",
        "experiment_code": "EXP-001",
        "objective": "Screen 6 sgRNA designs targeting VEGFR2 exon 7 using T7 endonuclease assay.",
        "hypothesis": "Two of six sgRNAs will achieve >70% editing efficiency based on GC content and secondary structure predictions.",
        "description": "HEK293T cells were transfected with pX330-GFP constructs carrying each sgRNA. Editing efficiency was assessed by T7E1 assay 72 h post-transfection.",
        "status": ExperimentStatus.IN_PROGRESS,
        "priority": "HIGH",
        "project_index": 0,
        "notes": [
            {
                "title": "Day 0 – Cell Seeding",
                "content": (
                    "## Cell Seeding (Day 0)\n\n"
                    "**Cell line:** HEK293T (ATCC CRL-11268)  \n"
                    "**Seeding density:** 2×10⁵ cells/well in 6-well plate  \n"
                    "**Media:** DMEM + 10% FBS + 1% Pen-Strep  \n\n"
                    "Cells were seeded at 70% confluency target. Incubated at 37°C, 5% CO₂.  \n\n"
                    "**Observations:** Cells appeared healthy. No contamination detected under microscope."
                ),
                "entry_type": "text",
                "tags": ["seeding", "HEK293T", "day-0"],
            },
            {
                "title": "Day 1 – Transfection with Lipofectamine 3000",
                "content": (
                    "## Transfection (Day 1)\n\n"
                    "**Reagent:** Lipofectamine 3000 (Thermo Fisher L3000015)  \n"
                    "**DNA amount:** 2 µg per well (pX330-GFP-sgRNA constructs)  \n"
                    "**Protocol:** Followed manufacturer's guidelines (Opti-MEM, 15 min complex formation)  \n\n"
                    "### Constructs Used:\n"
                    "| Well | sgRNA ID | Target Site |\n"
                    "|------|----------|-------------|\n"
                    "| A1   | sgRNA-01 | VEGFR2 ex7 pos 1204 |\n"
                    "| A2   | sgRNA-02 | VEGFR2 ex7 pos 1267 |\n"
                    "| A3   | sgRNA-03 | VEGFR2 ex7 pos 1312 |\n"
                    "| A4   | sgRNA-04 | VEGFR2 ex7 pos 1389 |\n"
                    "| B1   | sgRNA-05 | VEGFR2 ex7 pos 1421 |\n"
                    "| B2   | sgRNA-06 | VEGFR2 ex7 pos 1456 |\n"
                    "| B3   | Scramble | Non-targeting control |\n\n"
                    "**Transfection efficiency (GFP check at 24h):** ~62% GFP+ cells observed."
                ),
                "entry_type": "text",
                "tags": ["transfection", "Lipofectamine", "sgRNA"],
            },
            {
                "title": "Day 3 – T7E1 Assay Results",
                "content": (
                    "## T7E1 Endonuclease Assay (Day 3)\n\n"
                    "Genomic DNA extracted (DNeasy kit). PCR amplified the VEGFR2 exon 7 "
                    "region. T7E1 digest performed 37°C, 45 min.\n\n"
                    "### Editing Efficiency (ImageJ band densitometry):\n"
                    "| sgRNA | Uncut Band | Cut Bands | Efficiency |\n"
                    "|-------|-----------|-----------|------------|\n"
                    "| sgRNA-01 | 68% | 32% | **32%** |\n"
                    "| sgRNA-02 | 41% | 59% | **59%** |\n"
                    "| sgRNA-03 | 29% | 71% | **71%** ✓ |\n"
                    "| sgRNA-04 | 55% | 45% | **45%** |\n"
                    "| sgRNA-05 | 24% | 76% | **76%** ✓ |\n"
                    "| sgRNA-06 | 62% | 38% | **38%** |\n"
                    "| Scramble | 100% | 0% | **0%** |\n\n"
                    "**Conclusion:** sgRNA-03 and sgRNA-05 selected for next round. "
                    "Both exceed the 70% efficiency threshold. Forwarding to off-target analysis."
                ),
                "entry_type": "text",
                "tags": ["T7E1", "results", "efficiency"],
            },
        ],
    },
    {
        "title": "LNP Formulation Optimisation – mRNA Encapsulation Efficiency",
        "experiment_code": "EXP-002",
        "objective": "Optimise lipid nanoparticle (LNP) N/P ratio for maximum mRNA encapsulation efficiency.",
        "hypothesis": "An N/P ratio of 6:1 will yield >90% encapsulation efficiency.",
        "description": "Five LNP formulations with varying N/P ratios were prepared. Encapsulation efficiency measured by RiboGreen assay. Particle size and PDI measured by DLS.",
        "status": ExperimentStatus.COMPLETED,
        "priority": "HIGH",
        "project_index": 1,
        "notes": [
            {
                "title": "LNP Formulation – Experimental Design",
                "content": (
                    "## LNP Formulation Study Design\n\n"
                    "**mRNA:** H3N2 HA antigen mRNA (modified, 1.8 kb, IVT product)  \n"
                    "**Ionisable lipid:** DLin-MC3-DMA  \n"
                    "**Helper lipids:** DSPC, Cholesterol, PEG2000-DMG  \n\n"
                    "### N/P Ratios Tested:\n"
                    "| Formulation | N/P Ratio | Expected EE% |\n"
                    "|-------------|-----------|---------------|\n"
                    "| LNP-F01 | 3:1 | ~60% |\n"
                    "| LNP-F02 | 4:1 | ~75% |\n"
                    "| LNP-F03 | 6:1 | ~90% |\n"
                    "| LNP-F04 | 8:1 | ~92% |\n"
                    "| LNP-F05 | 10:1 | ~88% |\n\n"
                    "All formulations prepared by microfluidic mixing at 65°C using NanoAssemblr."
                ),
                "entry_type": "text",
                "tags": ["LNP", "formulation", "mRNA", "vaccine"],
            },
            {
                "title": "Results – DLS & RiboGreen Assay",
                "content": (
                    "## Results Summary\n\n"
                    "### DLS Measurements:\n"
                    "| Formulation | Z-Average (nm) | PDI | Zeta Potential (mV) |\n"
                    "|-------------|----------------|-----|----------------------|\n"
                    "| LNP-F01 | 112 ± 8 | 0.18 | -2.1 |\n"
                    "| LNP-F02 | 98 ± 5 | 0.15 | -1.8 |\n"
                    "| LNP-F03 | 87 ± 4 | 0.12 | -1.5 |\n"
                    "| LNP-F04 | 91 ± 6 | 0.14 | -1.2 |\n"
                    "| LNP-F05 | 105 ± 9 | 0.21 | -0.9 |\n\n"
                    "### RiboGreen Encapsulation Efficiency:\n"
                    "| Formulation | EE% |\n"
                    "|-------------|-----|\n"
                    "| LNP-F01 | 62.3% |\n"
                    "| LNP-F02 | 78.1% |\n"
                    "| **LNP-F03** | **91.4%** ✓ |\n"
                    "| LNP-F04 | 93.2% |\n"
                    "| LNP-F05 | 86.7% |\n\n"
                    "**Selected formulation:** LNP-F03 (N/P 6:1) — best balance of EE, particle size, and PDI."
                ),
                "entry_type": "results",
                "tags": ["DLS", "RiboGreen", "results", "LNP"],
            },
        ],
    },
    {
        "title": "16S rRNA V3-V4 Amplicon Sequencing – Cohort Batch 1",
        "experiment_code": "EXP-003",
        "objective": "Generate 16S amplicon sequencing data for first 40 subjects from the dietary intervention cohort.",
        "hypothesis": "High-fiber diet subjects will show elevated Firmicutes:Bacteroidetes ratio shift.",
        "description": "DNA extracted from stool samples. V3-V4 hypervariable region amplified with 341F/806R primers. Libraries prepared with Nextera XT and sequenced on Illumina MiSeq (2×300 bp).",
        "status": ExperimentStatus.IN_PROGRESS,
        "priority": "MEDIUM",
        "project_index": 2,
        "notes": [
            {
                "title": "DNA Extraction from Stool – QC Report",
                "content": (
                    "## Stool DNA Extraction QC\n\n"
                    "**Kit:** Qiagen QIAamp DNA Stool Mini Kit  \n"
                    "**Samples:** 40 subjects (20 high-fibre diet, 20 control)  \n"
                    "**Bead beating:** 5 m/s, 60 s × 3 cycles  \n\n"
                    "### QC Metrics (representative samples):\n"
                    "| Sample ID | A260/A280 | Conc (ng/µL) | RQN | Status |\n"
                    "|-----------|-----------|--------------|-----|--------|\n"
                    "| S001 | 1.82 | 48.3 | 7.1 | PASS |\n"
                    "| S002 | 1.79 | 52.1 | 8.0 | PASS |\n"
                    "| S003 | 1.91 | 31.5 | 6.8 | PASS |\n"
                    "| S004 | 1.64 | 12.8 | 4.2 | **FAIL** – low RQN |\n"
                    "| S005 | 1.88 | 44.7 | 7.5 | PASS |\n\n"
                    "Sample S004 flagged for re-extraction. All others passed QC thresholds (A260/A280 ≥ 1.7, conc ≥ 20 ng/µL, RQN ≥ 6.0)."
                ),
                "entry_type": "text",
                "tags": ["DNA-extraction", "QC", "16S", "stool"],
            },
        ],
    },
]


async def seed_experiments(tenant_id, users, project_ids, protocol_ids):
    pi_user = users.get("ashwink")
    researcher = users.get("sarahj")
    bio_user = users.get("rajp")
    experiment_ids = []

    for i, ed in enumerate(EXPERIMENTS_DATA):
        existing = await Experiment.find_one({"experiment_code": ed["experiment_code"]})
        if existing:
            log.info(f"  ↳ Experiment already exists: {ed['experiment_code']}")
            experiment_ids.append(existing.id)
            # Still try to seed notes if missing
            existing_notes = await NotebookEntry.find({"experiment_id": existing.id}).to_list()
            if not existing_notes:
                await _seed_notebook_entries(existing.id, tenant_id, users, ed["notes"])
            continue

        proj_id = project_ids[ed["project_index"]] if ed["project_index"] < len(project_ids) else project_ids[0]
        proto_id = protocol_ids[i] if i < len(protocol_ids) else None

        exp = Experiment(
            tenant_id=tenant_id,
            project_id=proj_id,
            owner_id=researcher.id if researcher else uuid4(),
            reviewer_id=pi_user.id if pi_user else None,
            protocol_id=proto_id,
            experiment_code=ed["experiment_code"],
            title=ed["title"],
            objective=ed["objective"],
            hypothesis=ed["hypothesis"],
            description=ed["description"],
            status=ed["status"],
            priority=ed["priority"],
            start_date=now(-14),
            planned_end_date=now(30),
        )
        await exp.insert()
        log.info(f"  ✓ Experiment: {exp.experiment_code}")
        experiment_ids.append(exp.id)

        # Add collaborator
        if bio_user:
            collab = ExperimentCollaborator(
                experiment_id=exp.id,
                user_id=bio_user.id,
                role="Bioinformatician",
                tenant_id=tenant_id,
            )
            await collab.insert()

        # Seed notebook entries
        await _seed_notebook_entries(exp.id, tenant_id, users, ed["notes"])

    return experiment_ids


async def _seed_notebook_entries(experiment_id, tenant_id, users, notes_data):
    researcher = users.get("sarahj")
    pi_user = users.get("ashwink")
    for nd in notes_data:
        entry = NotebookEntry(
            tenant_id=tenant_id,
            experiment_id=experiment_id,
            author_id=researcher.id if researcher else uuid4(),
            title=nd["title"],
            content=nd["content"],
            entry_type=nd.get("entry_type", "text"),
            version=1,
        )
        await entry.insert()
        log.info(f"    ✓ Notebook entry: {nd['title'][:50]}")

        for tag_str in nd.get("tags", []):
            tag = NotebookTag(entry_id=entry.id, tag=tag_str)
            await tag.insert()

        # Add a PI review comment
        if pi_user:
            comment = NotebookComment(
                entry_id=entry.id,
                author_id=pi_user.id,
                comment="Reviewed and confirmed. Data looks consistent with expected parameters.",
            )
            await comment.insert()


# =============================================================================
#  4. SAMPLE REGISTRY
# =============================================================================
async def seed_samples(tenant_id, users, experiment_ids):
    researcher = users.get("sarahj")

    # Sample Types
    types_data = [
        ("Genomic DNA", "Purified genomic DNA from mammalian cell lines or tissues."),
        ("Total RNA", "Total RNA extracted by TRIzol or column-based methods."),
        ("Cell Lysate", "Total protein lysate in RIPA buffer."),
        ("Serum", "Human or murine blood serum, centrifuged and aliquoted."),
        ("Stool", "Stool samples stabilised in OMNIgene-GUT tubes."),
        ("PBMC", "Peripheral Blood Mononuclear Cells isolated by Ficoll gradient."),
        ("Plasmid DNA", "Endotoxin-free maxiprep plasmid preparation."),
        ("mRNA", "In-vitro transcribed modified mRNA, capped and poly-A tailed."),
    ]
    type_ids = []
    for name, desc in types_data:
        existing = await SampleType.find_one({"name": name, "tenant_id": tenant_id})
        if existing:
            type_ids.append(existing.id)
        else:
            st = SampleType(tenant_id=tenant_id, name=name, description=desc)
            await st.insert()
            type_ids.append(st.id)
    log.info(f"  ✓ Sample types seeded: {len(types_data)}")

    # Storage Locations
    locations_data = [
        ("Freezer A – Shelf 1", "ULT-A", "S1"),
        ("Freezer A – Shelf 2", "ULT-A", "S2"),
        ("Freezer B – Shelf 1", "ULT-B", "S1"),
        ("LN₂ Dewar 01 – Rack 3", "LN2-01", "R3"),
        ("Fridge 4°C – Bench Lab 2", "FRIDGE-01", "BL2"),
    ]
    loc_ids = []
    for name, freezer, shelf in locations_data:
        existing = await SampleStorageLocation.find_one({"name": name, "tenant_id": tenant_id})
        if existing:
            loc_ids.append(existing.id)
        else:
            loc = SampleStorageLocation(
                tenant_id=tenant_id, name=name, freezer_unit=freezer, shelf=shelf
            )
            await loc.insert()
            loc_ids.append(loc.id)
    log.info(f"  ✓ Storage locations seeded: {len(locations_data)}")

    # Samples
    samples_data = [
        ("HEK293T gDNA – sgRNA-03 edited", "SMP-001", "available", 50.0, "µg", 0, 0, "Day 3 post-transfection harvest."),
        ("HEK293T gDNA – sgRNA-05 edited", "SMP-002", "available", 50.0, "µg", 0, 0, "Day 3 post-transfection harvest."),
        ("HEK293T gDNA – Scramble control", "SMP-003", "available", 50.0, "µg", 0, 1, "Non-targeting control."),
        ("H3N2 HA mRNA – IVT product", "SMP-004", "available", 200.0, "µg", 7, 2, "IVT with CleanCap AG, poly-A tailing."),
        ("LNP-F03 formulation – lot 001", "SMP-005", "in_use", 1.5, "mL", 7, 3, "Encapsulated mRNA LNP, N/P 6:1."),
        ("Subject S001 – stool DNA", "SMP-006", "available", 30.0, "µg", 4, 0, "Dietary intervention cohort, baseline."),
        ("Subject S002 – stool DNA", "SMP-007", "available", 40.0, "µg", 4, 0, "Dietary intervention cohort, baseline."),
        ("Subject S003 – stool DNA", "SMP-008", "available", 25.0, "µg", 4, 1, "Dietary intervention cohort, week 4."),
        ("PBMC – Donor HC-07", "SMP-009", "frozen", 5.0, "mL", 5, 3, "10⁷ cells/mL in 10% DMSO. Slow frozen."),
        ("BRAF V600E cell lysate – A375", "SMP-010", "available", 200.0, "µg", 2, 1, "Total lysate in RIPA, 2 µg/µL."),
        ("Anti-VEGFR2 antibody – lot 22B", "SMP-011", "available", 50.0, "µg", 0, 4, "Rabbit polyclonal, aliquoted."),
        ("pX330-GFP-sgRNA03 plasmid", "SMP-012", "available", 100.0, "µg", 6, 2, "Endotoxin-free maxiprep."),
    ]

    existing_count = await Sample.find({"tenant_id": tenant_id}).count()
    if existing_count >= len(samples_data):
        log.info(f"  ↳ Samples already seeded ({existing_count} found).")
        return

    user_id = researcher.id if researcher else uuid4()
    exp_id = experiment_ids[0] if experiment_ids else None

    for name, code, status, qty, unit, type_idx, loc_idx, notes in samples_data:
        smp = Sample(
            tenant_id=tenant_id,
            experiment_id=exp_id,
            sample_type_id=type_ids[type_idx] if type_idx < len(type_ids) else None,
            location_id=loc_ids[loc_idx] if loc_idx < len(loc_ids) else None,
            owner_id=user_id,
            name=name,
            sample_code=code,
            barcode=f"BC{code.split('-')[1]}",
            status=status,
            quantity=qty,
            unit=unit,
            metadata_json={"notes": notes},
        )
        await smp.insert()

        custody = SampleChainOfCustody(
            sample_id=smp.id,
            user_id=user_id,
            action="created",
            notes=f"Initial registration: {notes}",
        )
        await custody.insert()

    log.info(f"  ✓ Samples seeded: {len(samples_data)}")


# =============================================================================
#  5. INVENTORY MANAGEMENT
# =============================================================================
async def seed_inventory(tenant_id, users):
    researcher = users.get("sarahj")
    user_id = researcher.id if researcher else uuid4()

    # Categories
    cats = [
        ("Reagents", "Chemical reagents, enzymes, and biological reagents."),
        ("Consumables", "Pipette tips, tubes, plates, and disposable labware."),
        ("Kits", "Commercial assay kits with all components included."),
        ("Equipment Parts", "Spare parts and accessories for lab equipment."),
        ("Safety & PPE", "Personal protective equipment and safety supplies."),
    ]
    cat_ids = {}
    for name, desc in cats:
        existing = await InventoryCategory.find_one({"name": name, "tenant_id": tenant_id})
        if existing:
            cat_ids[name] = existing.id
        else:
            c = InventoryCategory(tenant_id=tenant_id, name=name, description=desc)
            await c.insert()
            cat_ids[name] = c.id

    # Suppliers
    suppliers = [
        ("Thermo Fisher Scientific", "orders-india@thermofisher.com"),
        ("Sigma-Aldrich / Merck", "india.orders@merckgroup.com"),
        ("Qiagen", "qs.india@qiagen.com"),
        ("BD Biosciences", "bd.india@bd.com"),
        ("New England Biolabs", "neb.india@neb.com"),
    ]
    sup_ids = {}
    for name, email in suppliers:
        existing = await InventorySupplier.find_one({"name": name, "tenant_id": tenant_id})
        if existing:
            sup_ids[name] = existing.id
        else:
            s = InventorySupplier(tenant_id=tenant_id, name=name, contact_email=email)
            await s.insert()
            sup_ids[name] = s.id

    # Locations
    inv_locs = [
        ("Lab 101 – Chemical Cabinet A", "Lab 101"),
        ("Lab 101 – -20°C Freezer", "Lab 101"),
        ("Lab 102 – -80°C ULT Freezer", "Lab 102"),
        ("Lab 103 – Consumables Shelf", "Lab 103"),
        ("Cold Room 4°C – Reagent Rack", "Cold Room"),
    ]
    inv_loc_ids = []
    for name, room in inv_locs:
        existing = await InventoryLocation.find_one({"name": name, "tenant_id": tenant_id})
        if existing:
            inv_loc_ids.append(existing.id)
        else:
            l = InventoryLocation(tenant_id=tenant_id, name=name, room=room)
            await l.insert()
            inv_loc_ids.append(l.id)

    log.info("  ✓ Inventory categories, suppliers, and locations seeded.")

    # Inventory Items
    items_data = [
        # (name, sku, cat, supplier, loc_idx, stock, reorder, unit, expiry_offset_days)
        ("TRIzol Reagent (100 mL)", "TF-15596018", "Reagents", "Thermo Fisher Scientific", 1, 8.0, 2.0, "bottle", 365),
        ("Taq DNA Polymerase (500 U)", "NEB-M0273S", "Reagents", "New England Biolabs", 1, 12.0, 3.0, "vial", 365),
        ("RNase-Free Water (500 mL)", "SA-W4502", "Reagents", "Sigma-Aldrich / Merck", 4, 5.0, 2.0, "bottle", 730),
        ("RIPA Lysis Buffer (50 mL)", "SA-R0278", "Reagents", "Sigma-Aldrich / Merck", 0, 3.0, 2.0, "bottle", 365),
        ("Lipofectamine 3000 (1.5 mL)", "TF-L3000015", "Reagents", "Thermo Fisher Scientific", 1, 4.0, 1.0, "kit", 365),
        ("Protease Inhibitor Cocktail", "SA-P8340", "Reagents", "Sigma-Aldrich / Merck", 2, 6.0, 2.0, "vial", 730),
        ("TMB Substrate Solution (100 mL)", "TF-34028", "Reagents", "Thermo Fisher Scientific", 4, 7.0, 2.0, "bottle", 180),
        ("Opti-MEM (500 mL)", "TF-31985062", "Reagents", "Thermo Fisher Scientific", 4, 9.0, 3.0, "bottle", 365),
        ("Ficoll-Paque PLUS (500 mL)", "SA-GE17-1440-03", "Reagents", "Sigma-Aldrich / Merck", 4, 3.0, 1.0, "bottle", 365),
        ("DLin-MC3-DMA Lipid (10 mg)", "SA-900407", "Reagents", "Sigma-Aldrich / Merck", 2, 2.0, 1.0, "vial", 730),
        # Kits
        ("DNeasy Blood & Tissue Kit (250)", "QG-69506", "Kits", "Qiagen", 0, 2.0, 1.0, "kit", 730),
        ("QIAamp DNA Stool Mini Kit (50)", "QG-51504", "Kits", "Qiagen", 0, 1.0, 1.0, "kit", 730),
        ("Nextera XT Library Prep Kit", "SA-FC-131-1024", "Kits", "Sigma-Aldrich / Merck", 2, 1.0, 1.0, "kit", 365),
        ("BCA Protein Assay Kit (500)", "TF-23225", "Kits", "Thermo Fisher Scientific", 0, 3.0, 1.0, "kit", 730),
        ("RiboGreen RNA Assay Kit", "TF-R11490", "Kits", "Thermo Fisher Scientific", 2, 1.0, 1.0, "kit", 365),
        # Consumables
        ("1000 µL Pipette Tips (10×96)", "TF-02-707-404", "Consumables", "Thermo Fisher Scientific", 3, 25.0, 5.0, "box", 3650),
        ("200 µL Pipette Tips (10×96)", "TF-02-707-402", "Consumables", "Thermo Fisher Scientific", 3, 30.0, 5.0, "box", 3650),
        ("1.5 mL Eppendorf Tubes (1000)", "SA-T9661", "Consumables", "Sigma-Aldrich / Merck", 3, 15.0, 3.0, "pack", 3650),
        ("96-Well Flat-Bottom Plate (50)", "BD-353072", "Consumables", "BD Biosciences", 3, 8.0, 2.0, "pack", 3650),
        ("0.45 µm PVDF Membrane (10)", "SA-IPVH00010", "Consumables", "Sigma-Aldrich / Merck", 3, 4.0, 2.0, "pack", 3650),
    ]

    existing_count = await InventoryItem.find({"tenant_id": tenant_id}).count()
    if existing_count >= len(items_data):
        log.info(f"  ↳ Inventory items already seeded ({existing_count} found).")
        return

    for name, sku, cat_name, sup_name, loc_idx, stock, reorder, unit, exp_days in items_data:
        item = InventoryItem(
            tenant_id=tenant_id,
            category_id=cat_ids.get(cat_name),
            supplier_id=sup_ids.get(sup_name),
            location_id=inv_loc_ids[loc_idx] if loc_idx < len(inv_loc_ids) else None,
            name=name,
            sku=sku,
            status="in_stock" if stock > reorder else "low_stock",
            current_stock=stock,
            reorder_level=reorder,
            unit=unit,
        )
        await item.insert()

        batch = InventoryBatch(
            item_id=item.id,
            batch_number=f"BT-{sku[-6:]}",
            quantity=stock,
            expiry_date=now(exp_days),
        )
        await batch.insert()

        txn = InventoryTransaction(
            item_id=item.id,
            user_id=user_id,
            transaction_type="receipt",
            quantity_changed=stock,
            notes=f"Initial stock entry – {name}",
        )
        await txn.insert()

    log.info(f"  ✓ Inventory items seeded: {len(items_data)}")


# =============================================================================
#  6. INSTRUMENT MANAGEMENT
# =============================================================================
async def seed_instruments(tenant_id, users):
    researcher = users.get("sarahj")
    pi_user = users.get("ashwink")
    user_id = researcher.id if researcher else uuid4()

    inst_types_data = [
        ("PCR Thermocycler", "For thermal cycling of PCR reactions."),
        ("Fluorescence Spectrophotometer / NanoDrop", "For nucleic acid quantification."),
        ("Flow Cytometer", "For cell sorting and immunophenotyping."),
        ("Plate Reader", "Absorbance, fluorescence, luminescence multi-mode plate reader."),
        ("Next-Generation Sequencer", "High-throughput DNA/RNA sequencing."),
        ("Ultracentrifuge", "For density-gradient centrifugation and nanoparticle pelleting."),
        ("Confocal Microscope", "Fluorescence confocal laser scanning microscopy."),
        ("Microfluidic Mixer", "Automated LNP and nanoparticle formulation."),
    ]
    type_ids = []
    for name, desc in inst_types_data:
        existing = await InstrumentType.find_one({"name": name, "tenant_id": tenant_id})
        if existing:
            type_ids.append(existing.id)
        else:
            it = InstrumentType(tenant_id=tenant_id, name=name, description=desc)
            await it.insert()
            type_ids.append(it.id)

    instruments_data = [
        # (name, asset_id, model, serial, type_idx, cal_due_offset, status)
        ("Applied Biosystems ProFlex 96-Well PCR", "INST-PCR-01", "ProFlex 3×32", "SN-AB3032-0041", 0, 90, "operational"),
        ("Thermo NanoDrop 2000c UV-Vis", "INST-NDR-01", "NanoDrop 2000c", "SN-ND2000C-117", 1, 180, "operational"),
        ("BD LSRFortessa X-20 Flow Cytometer", "INST-FCM-01", "LSRFortessa X-20", "SN-LSRX20-0089", 2, 60, "operational"),
        ("BMG CLARIOstar Plus Plate Reader", "INST-PLR-01", "CLARIOstar Plus", "SN-BMG-CL-0033", 3, 180, "operational"),
        ("Illumina MiSeq System", "INST-SEQ-01", "MiSeq v3", "SN-MQ00501", 4, 365, "operational"),
        ("Beckman Coulter Optima XPN Ultracentrifuge", "INST-UCF-01", "Optima XPN-80", "SN-XPN80-1124", 5, 90, "operational"),
        ("Zeiss LSM 900 Confocal Microscope", "INST-CONF-01", "LSM 900", "SN-LSM9-0022", 6, 365, "operational"),
        ("Precision NanoSystems NanoAssemblr Ignite", "INST-MFM-01", "NanoAssemblr Ignite", "SN-NAI-0015", 7, 180, "operational"),
        ("Applied Biosystems QuantStudio 7 qPCR", "INST-QPC-01", "QuantStudio 7 Flex", "SN-QS7F-0098", 0, 90, "operational"),
        ("Eppendorf Mastercycler nexus X2", "INST-PCR-02", "nexus X2 Gradient", "SN-EPNX2-0205", 0, 90, "under_maintenance"),
    ]

    existing_count = await Instrument.find({"tenant_id": tenant_id}).count()
    if existing_count >= len(instruments_data):
        log.info(f"  ↳ Instruments already seeded ({existing_count} found).")
        return

    for name, asset_id, model, serial, type_idx, cal_due, status in instruments_data:
        inst = Instrument(
            tenant_id=tenant_id,
            instrument_type_id=type_ids[type_idx] if type_idx < len(type_ids) else None,
            name=name,
            asset_id=asset_id,
            model=model,
            serial_number=serial,
            operational_status=status,
            availability_status="available" if status == "operational" else "unavailable",
            is_operational=(status == "operational"),
            calibration_due_date=now(cal_due),
            maintenance_due_date=now(cal_due + 30),
        )
        await inst.insert()

        # Calibration record
        cal = InstrumentCalibration(
            instrument_id=inst.id,
            calibrated_at=now(-cal_due),
            status="passed",
            notes=f"Periodic calibration performed. Next due in {cal_due} days.",
        )
        await cal.insert()

        # Maintenance record
        maint = InstrumentMaintenance(
            instrument_id=inst.id,
            performed_at=now(-30),
            notes="Routine preventive maintenance. Cleaned optical components, replaced consumable parts.",
        )
        await maint.insert()

        # Reservation
        if pi_user and status == "operational":
            res = InstrumentReservation(
                instrument_id=inst.id,
                user_id=user_id,
                start_time=now(3),
                end_time=now(3) + timedelta(hours=4),
            )
            await res.insert()

    log.info(f"  ✓ Instruments seeded: {len(instruments_data)}")


# =============================================================================
#  7. SEQUENCE MANAGEMENT
# =============================================================================
SEQUENCES_DATA = [
    {
        "name": "VEGFR2 Exon 7 – sgRNA-03 Target Region",
        "sequence_type": "DNA",
        "sequence_data": "ATGGCAGCAGTGGCGGTGGCGGCGGCAATGAAGAGCAACATCAAGGAGGCCCTGCAGCTGCAGCAGCTGCAGCAGCTGCAGCAGCTGCAGCAGCTGCAGCAGCTGCAGTGGAGCAGCAGCAGCAACAGCAGCAGCATCACCAGCAGCAGCAGCAGCAGCACCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAG",
        "gc_content": 57.2,
        "status": "active",
        "annotations": [
            ("sgRNA-03 PAM Site", 48, 71),
            ("Exon 7 Splice Donor", 180, 220),
        ],
        "analysis": {
            "type": "off_target_prediction",
            "result": {"tool": "Cas-OFFinder", "off_targets_found": 2, "max_mismatches": 3, "risk": "low"}
        },
    },
    {
        "name": "VEGFR2 Exon 7 – sgRNA-05 Target Region",
        "sequence_type": "DNA",
        "sequence_data": "TGCTGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAG",
        "gc_content": 58.1,
        "status": "active",
        "annotations": [
            ("sgRNA-05 Guide Sequence", 1, 20),
            ("PAM – NGG", 21, 23),
        ],
        "analysis": {
            "type": "off_target_prediction",
            "result": {"tool": "Cas-OFFinder", "off_targets_found": 0, "max_mismatches": 3, "risk": "very_low"}
        },
    },
    {
        "name": "H3N2 Haemagglutinin (HA) mRNA – Modified",
        "sequence_type": "mRNA",
        "sequence_data": "AUGGAAAGAAUAAAAGUGCUUAUUUCUGCUAUUUUAGCUAUUAGAGCAAGUGCAAACGGAACGAAAACUGAACAGAAACAAGCCAUAGAUGAAAGAGAGAACGGAAAGAGUGGUCUGCUGGUGAAGGAGACAGCAAGAGCUGAAAGAUAUGAGAGUGACAACCUGAACAGAACAGAACGUGAAAGUGACAGCAUUCAAGAAGACAAGGCUAAUGAAAACUAAGCUGACAAAAGCUUCUGAGCAGAUUGAGGAUUGGAUUGAAGACAAAAGAGAGCUGAAACAGACAAAAGAAGCCUGAGACACUUGAAGAAGAGAGAGAAUGGAGAAACUGAGAGAGCUGAGCAACUGAGAGAGCUUAACAGAGCCUGAAAGAAAGCUGAAAGAAGUGAGA",
        "gc_content": 46.8,
        "status": "active",
        "annotations": [
            ("5' UTR", 1, 50),
            ("Signal Peptide", 51, 110),
            ("HA1 Subunit", 111, 980),
            ("HA2 Subunit", 981, 1680),
            ("Transmembrane Domain", 1540, 1610),
            ("3' UTR", 1681, 1750),
        ],
        "analysis": {
            "type": "codon_optimisation",
            "result": {"original_cai": 0.63, "optimised_cai": 0.91, "tool": "GenSmart", "modified_nucleotides": ["N1-methylpseudouridine"]}
        },
    },
    {
        "name": "16S rRNA V3-V4 Amplicon – 341F Primer",
        "sequence_type": "DNA",
        "sequence_data": "CCTACGGGNGGCWGCAG",
        "gc_content": 64.7,
        "status": "active",
        "annotations": [
            ("341F Forward Primer", 1, 17),
        ],
        "analysis": {
            "type": "primer_analysis",
            "result": {"tm": 57.3, "gc_percent": 64.7, "hairpin_dg": -0.4, "dimer_dg": -3.1, "specificity": "V3 region 16S rRNA"}
        },
    },
    {
        "name": "16S rRNA V3-V4 Amplicon – 806R Primer",
        "sequence_type": "DNA",
        "sequence_data": "GGACTACHVGGGTWTCTAAT",
        "gc_content": 45.0,
        "status": "active",
        "annotations": [
            ("806R Reverse Primer", 1, 20),
        ],
        "analysis": {
            "type": "primer_analysis",
            "result": {"tm": 54.1, "gc_percent": 45.0, "hairpin_dg": -0.1, "dimer_dg": -2.8, "specificity": "V4 region 16S rRNA"}
        },
    },
    {
        "name": "pX330-GFP-sgRNA03 Plasmid – hU6 Promoter",
        "sequence_type": "DNA",
        "sequence_data": "GGATCGGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAGTTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTCTGGCCTTTTCCAT",
        "gc_content": 52.3,
        "status": "active",
        "annotations": [
            ("hU6 Promoter", 1, 240),
            ("sgRNA Scaffold", 241, 360),
            ("CMV Enhancer", 361, 420),
            ("SpCas9 ORF", 421, 4600),
        ],
        "analysis": {
            "type": "plasmid_map",
            "result": {"plasmid_size_kb": 8.4, "resistance": "Ampicillin", "copy_number": "high", "origin": "pUC"}
        },
    },
    {
        "name": "BRAF V600E Oncogenic Variant – Kinase Domain",
        "sequence_type": "DNA",
        "sequence_data": "ATGACTGAATATAAACTTGTGGTAGTTGGAGCTGGTGGCGTAGGCAAGAGTGCCTTGACGATACAGCTAATTCAGAATCATTTTGTGGAAGACTATGATTTTTGCCACAGAAATAATTTTTACAGACACATTTCATTTCTGAATATTTTTCATACATTTAAACCTGATGTTTTTTTATTTGCTGATATAGAACAACAAAATAGCAGCAGCAAAAAAGTCTTCTCAAGGGCAGCTTCTAAAGCAGAAGACGGAAACCAGCAGCATCAAGACATCAGAGCAGCCCATGTGGGCTCCTGTTTGTTTTTTGATGACTTATAGCATTTCTGAAACATTTCTTGAAGAAGACATTTTTATAATGAAAGAG",
        "gc_content": 49.6,
        "status": "active",
        "annotations": [
            ("Kinase Domain", 1, 900),
            ("V600E Mutation Site", 598, 601),
            ("DFG Motif", 680, 695),
            ("Activation Loop", 690, 730),
        ],
        "analysis": {
            "type": "variant_annotation",
            "result": {"variant": "V600E", "cosmic_id": "COSV56056643", "clinical_significance": "Pathogenic", "drug_sensitivity": ["Vemurafenib", "Dabrafenib"]}
        },
    },
]


async def seed_sequences(tenant_id, users, experiment_ids):
    bio_user = users.get("rajp")
    user_id = bio_user.id if bio_user else uuid4()
    exp_id = experiment_ids[0] if experiment_ids else None

    existing_count = await Sequence.find({"tenant_id": tenant_id}).count()
    if existing_count >= len(SEQUENCES_DATA):
        log.info(f"  ↳ Sequences already seeded ({existing_count} found).")
        return

    for sd in SEQUENCES_DATA:
        seq = Sequence(
            tenant_id=tenant_id,
            experiment_id=exp_id,
            name=sd["name"],
            sequence_type=sd["sequence_type"],
            sequence_data=sd["sequence_data"],
            length=len(sd["sequence_data"]),
            status=sd["status"],
            gc_content=sd["gc_content"],
        )
        await seq.insert()

        for label, start, end in sd.get("annotations", []):
            ann = SequenceAnnotation(
                sequence_id=seq.id, label=label, start_pos=start, end_pos=end
            )
            await ann.insert()

        if sd.get("analysis"):
            result = SequenceAnalysisResult(
                sequence_id=seq.id,
                analysis_type=sd["analysis"]["type"],
                result_data=sd["analysis"]["result"],
            )
            await result.insert()

    log.info(f"  ✓ Sequences seeded: {len(SEQUENCES_DATA)}")


# =============================================================================
#  MAIN
# =============================================================================
async def main():
    print("\n" + "=" * 60)
    print("  GENQUANTAA ELN — Demo Data Seeding Script")
    print("=" * 60 + "\n")

    client = await init_db()

    try:
        # Get DEFAULT tenant
        tenant = await Tenant.find_one({"code": "DEFAULT"})
        if not tenant:
            print("❌  ERROR: DEFAULT tenant not found.")
            print("   Please start the backend server once first to auto-create the tenant and users.")
            return

        log.info(f"Using tenant: {tenant.name} ({tenant.id})")

        users = await get_users(tenant.id)
        if not users:
            print("❌  ERROR: No users found for the DEFAULT tenant.")
            print("   Please start the backend server once first so default users are auto-seeded.")
            return

        log.info(f"Found users: {list(users.keys())}")

        print("\n[1/7] Seeding Projects…")
        project_ids = await seed_projects(tenant.id, users)

        print("\n[2/7] Seeding Protocols…")
        protocol_ids = await seed_protocols(tenant.id, users, project_ids)

        print("\n[3/7] Seeding Experiments + ELN Notebook Entries…")
        experiment_ids = await seed_experiments(tenant.id, users, project_ids, protocol_ids)

        print("\n[4/7] Seeding Sample Registry…")
        await seed_samples(tenant.id, users, experiment_ids)

        print("\n[5/7] Seeding Inventory Management…")
        await seed_inventory(tenant.id, users)

        print("\n[6/7] Seeding Instrument Management…")
        await seed_instruments(tenant.id, users)

        print("\n[7/7] Seeding Sequences (Management + Viewer)…")
        await seed_sequences(tenant.id, users, experiment_ids)

        print("\n" + "=" * 60)
        print("  [OK] Demo data seeded successfully!")
        print("=" * 60)
        print("\n  Login credentials (all users share the same password):")
        print("  +-------------------------------------+-------------+--------------------+")
        print("  | Email                               | Role        | Password           |")
        print("  +-------------------------------------+-------------+--------------------+")
        print("  | admin@eln.com                       | Admin       | Admin@12345678     |")
        print("  | ashwin.kumar@eln.com                | PI          | Admin@12345678     |")
        print("  | sarah.johnson@eln.com               | Researcher  | Admin@12345678     |")
        print("  | raj.patel@eln.com                   | Bioinformat | Admin@12345678     |")
        print("  | ananya.sharma@eln.com               | QA          | Admin@12345678     |")
        print("  | saikiran@eln.com                    | Admin       | Admin@12345678     |")
        print("  +-------------------------------------+-------------+--------------------+")
        print()

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
