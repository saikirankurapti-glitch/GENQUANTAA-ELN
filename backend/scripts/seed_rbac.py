import asyncio
import logging
import time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

# Explicitly load environment variables or set configurations if needed
from app.db.base import AsyncSessionLocal
from app.crud.crud_tenant import tenant as tenant_repo
from app.crud.crud_role import role as role_repo
from app.crud.crud_permission import permission as permission_repo
from app.crud.crud_role_permission import role_permission as role_permission_repo
from app.schemas.tenant import TenantCreate
from app.schemas.rbac import RoleCreate, PermissionCreate
from app.db.enums import RoleStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ==============================================================================
# PERMISSION DEFINITIONS
# ==============================================================================
PERMISSIONS_DATA = [
    ("tenant", "tenant", "read"), ("tenant", "tenant", "create"), 
    ("tenant", "tenant", "update"), ("tenant", "tenant", "delete"),
    
    ("rbac", "role", "read"), ("rbac", "role", "create"), 
    ("rbac", "role", "update"), ("rbac", "role", "delete"),
    
    ("rbac", "permission", "read"), ("rbac", "permission", "create"),
    ("rbac", "permission", "update"), ("rbac", "permission", "delete"),
    
    ("rbac", "role_permission", "assign"), ("rbac", "role_permission", "remove"), 
    ("rbac", "role_permission", "replace"),
    
    ("project", "project", "read"), ("project", "project", "create"),
    ("study", "study", "read"), ("study", "study", "create"),
    ("experiment", "experiment", "read"), ("experiment", "experiment", "create"),
    ("sample", "sample", "read"), ("sample", "sample", "create"),
    ("inventory", "inventory", "transfer"),
    
    ("workflow", "workflow", "approve"),
    ("audit", "logs", "read"),
    ("signature", "signature", "sign")
]

# ==============================================================================
# ROLE DEFINITIONS
# ==============================================================================
ROLES_DATA = [
    {"name": "System Administrator", "code": "system.admin", "desc": "Full platform administration."},
    {"name": "Organization Administrator", "code": "org.admin", "desc": "Manages organization resources and users."},
    {"name": "Principal Investigator", "code": "pi", "desc": "Oversees research, projects, and study integrity."},
    {"name": "Research Scientist", "code": "scientist", "desc": "Performs experiments and generates data."},
    {"name": "Lab Technician", "code": "technician", "desc": "Executes assays and manages samples/inventory."},
    {"name": "QA Reviewer", "code": "qa.reviewer", "desc": "Ensures compliance and reviews audit logs."},
    {"name": "Viewer", "code": "viewer", "desc": "Read-only access across the platform."},
]

def map_role_permissions(all_perms_dict: dict) -> dict:
    """Map expected permissions to roles based on domain logic."""
    all_codes = list(all_perms_dict.keys())
    
    def get_ids(codes):
        return [all_perms_dict[c] for c in codes if c in all_perms_dict]
        
    mappings = {
        # System Admin gets literally everything
        "system.admin": get_ids(all_codes),
        
        # Org Admin gets everything except global RBAC permissions or global tenant management
        "org.admin": get_ids([c for c in all_codes if not c.startswith("tenant") and not c.startswith("rbac.permission")]),
        
        "pi": get_ids([
            "project.project.read", "project.project.create", 
            "study.study.read", "study.study.create", 
            "experiment.experiment.read", "experiment.experiment.create", 
            "workflow.workflow.approve"
        ]),
        
        "scientist": get_ids([
            "experiment.experiment.read", "experiment.experiment.create", 
            "sample.sample.read", "sample.sample.create"
        ]),
        
        "technician": get_ids([
            "sample.sample.read", "sample.sample.create", 
            "inventory.inventory.transfer"
        ]),
        
        "qa.reviewer": get_ids([
            "audit.logs.read", "signature.signature.sign", "workflow.workflow.approve",
            "project.project.read", "study.study.read", "experiment.experiment.read", "sample.sample.read"
        ]),
        
        # Viewer gets any read permission
        "viewer": get_ids([c for c in all_codes if "read" in c])
    }
    return mappings

async def seed_data():
    start_time = time.time()
    logger.info("Starting RBAC Seed Process...")
    
    stats = {
        "permissions_created": 0,
        "roles_created": 0,
        "assignments_created": 0,
        "skipped_existing": 0
    }
    
    async with AsyncSessionLocal() as db:
        
        # 1. Ensure System Tenant exists (Required for Roles)
        tenant_code = "SYSTEM"
        system_tenant = await tenant_repo.get_by_code(db, code=tenant_code)
        if not system_tenant:
            tenant_in = TenantCreate(name="System Master Tenant", code=tenant_code, description="Master tenant for global configuration.")
            system_tenant = await tenant_repo.create(db, obj_in=tenant_in)
            logger.info("Created missing SYSTEM tenant.")
        else:
            logger.info("SYSTEM tenant already exists.")

        # 2. Seed Permissions
        logger.info("Seeding Permissions...")
        permission_map = {}
        for mod, res, act in PERMISSIONS_DATA:
            code = f"{mod}.{res}.{act}"
            existing = await permission_repo.get_by_code(db, code=code)
            if existing:
                stats["skipped_existing"] += 1
                permission_map[code] = existing.id
            else:
                perm_in = PermissionCreate(module=mod, resource=res, action=act, code=code, description=f"Allows {act} on {res} inside {mod}")
                new_perm = await permission_repo.create(db, obj_in=perm_in)
                stats["permissions_created"] += 1
                permission_map[code] = new_perm.id
                logger.info(f"Created Permission: {code}")

        # 3. Seed Roles
        logger.info("Seeding System Roles...")
        role_id_map = {}
        for r_data in ROLES_DATA:
            existing_role = await role_repo.get_by_code(db, code=r_data["code"], tenant_id=system_tenant.id)
            if existing_role:
                stats["skipped_existing"] += 1
                role_id_map[r_data["code"]] = existing_role.id
            else:
                role_in = RoleCreate(
                    name=r_data["name"],
                    code=r_data["code"],
                    description=r_data["desc"],
                    is_system=True,
                    status=RoleStatus.ACTIVE,
                    tenant_id=system_tenant.id
                )
                new_role = await role_repo.create(db, obj_in=role_in)
                stats["roles_created"] += 1
                role_id_map[r_data["code"]] = new_role.id
                logger.info(f"Created Role: {r_data['code']}")

        # 4. Map Permissions to Roles
        logger.info("Assigning Permissions to Roles...")
        role_perm_mappings = map_role_permissions(permission_map)
        
        for role_code, perm_ids in role_perm_mappings.items():
            role_id = role_id_map.get(role_code)
            if not role_id:
                continue
                
            # Fetch existing to avoid duplicates
            existing_perms = await role_permission_repo.get_permissions_for_role(db, role_id=role_id)
            existing_perm_ids = {p.id for p in existing_perms}
            
            to_assign = [pid for pid in perm_ids if pid not in existing_perm_ids]
            
            if to_assign:
                count = await role_permission_repo.assign_permissions_bulk(db, role_id=role_id, permission_ids=to_assign)
                stats["assignments_created"] += count
                logger.info(f"Assigned {count} new permissions to role {role_code}")
            else:
                stats["skipped_existing"] += len(perm_ids)

    execution_time = round(time.time() - start_time, 2)
    
    print("\n" + "="*50)
    print("RBAC SEED SUMMARY")
    print("="*50)
    print(f"Roles Created:       {stats['roles_created']}")
    print(f"Permissions Created: {stats['permissions_created']}")
    print(f"Assignments Created: {stats['assignments_created']}")
    print(f"Skipped Existing:    {stats['skipped_existing']}")
    print(f"Execution Time:      {execution_time} seconds")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(seed_data())
