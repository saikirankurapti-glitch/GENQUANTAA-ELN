import { User } from '../types/auth';
import { ViewMode } from '../types';
import { getUserRole } from './userUtils';

export type RoleName = 
  | 'Admin' 
  | 'PI' 
  | 'Researcher' 
  | 'Scientist'
  | 'Lab Technician' 
  | 'Bioinformatician' 
  | 'QA' 
  | 'Viewer';

export const isUserAdmin = (user?: User | null): boolean => {
  if (!user) return false;
  const role = getUserRole(user).toLowerCase();
  return role.includes('admin') || role.includes('super');
};

export const normalizeRole = (user?: User | null): string => {
  if (!user) return 'Researcher';
  const role = getUserRole(user).trim();
  if (role === 'PI / Manager' || role === 'Lab Manager' || role === 'Project Owner') return 'PI';
  if (role === 'Scientist') return 'Researcher';
  return role;
};

export const canViewViewMode = (user: User | null, view: ViewMode): boolean => {
  if (!user) return true; // Default allow during unauthenticated landing
  
  if (view === 'admin') {
    return isUserAdmin(user);
  }

  // All logged-in users have read access to standard ELN research modules
  return true;
};

// CRUD Capability Checkers (Read-only enforcement for QA and Viewer)
export const canCreate = (user?: User | null): boolean => {
  const role = normalizeRole(user);
  if (role === 'QA' || role === 'Viewer') return false;
  return true;
};

export const canEdit = (user?: User | null): boolean => {
  const role = normalizeRole(user);
  if (role === 'QA' || role === 'Viewer') return false;
  return true;
};

export const canDelete = (user?: User | null): boolean => {
  const role = normalizeRole(user);
  if (role === 'QA' || role === 'Viewer') return false;
  return isUserAdmin(user) || role === 'PI';
};

// Explicit Sprint PDF Permission Helper Functions
export const canManageUsers = (user?: User | null): boolean => isUserAdmin(user);
export const canManageRoles = (user?: User | null): boolean => isUserAdmin(user);
export const canViewAuditLogs = (user?: User | null): boolean => {
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'QA';
};
export const canAccessAdminPanel = (user?: User | null): boolean => isUserAdmin(user);

export const canCreateProjects = (user?: User | null): boolean => {
  if (!user || !canCreate(user)) return false;
  const role = normalizeRole(user);
  // Only Admin and PI can create projects.
  // Researchers / Bioinformaticians are assigned to projects by a PI or Admin.
  return isUserAdmin(user) || role === 'PI';
};

export const canEditProjects = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  // Researchers / Bioinformaticians can edit experiments within a project they are assigned to,
  // but cannot rename or modify the project itself.
  return isUserAdmin(user) || role === 'PI';
};

export const canDeleteProjects = (user?: User | null): boolean => {
  if (!user || !canDelete(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI';
};

export const canCreateExperiment = (user?: User | null): boolean => {
  if (!user || !canCreate(user)) return false;
  const role = normalizeRole(user);
  // Only Admin and PI can create / initiate new experiments
  // Researchers and Scientists work within assigned experiments to document results
  return isUserAdmin(user) || role === 'PI';
};

export const canEditExperiment = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  // Admin, PI, Researcher, Scientist, and Bioinformatician can edit/document notebook entries
  return isUserAdmin(user) || ['PI', 'Researcher', 'Scientist', 'Bioinformatician'].includes(role);
};

// Team / collaborator management: only Admin and PI can add/remove members
export const canManageTeam = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI';
};

export const canManageInventory = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'Researcher' || role === 'Lab Technician';
};

export const canManageProtocols = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI' || role === 'Researcher';
};

export const canManageSequences = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'Bioinformatician' || role === 'Researcher';
};

// QA Role Comment Visibility and Annotation Permissions
export const isUserQA = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role === 'QA' || isUserAdmin(user);
};

export const isStrictlyQA = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role === 'QA';
};

export const isStrictlyViewer = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role === 'Viewer';
};

export const canUseAICopilot = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  if (role === 'QA' || role === 'Viewer') return false;
  return true;
};

// Researchers & Authors MUST be able to view QA comments to resolve them!
export const canViewQAComments = (user?: User | null): boolean => {
  if (!user) return false;
  return true;
};

// Only QA and Admin can initiate new QA audit review threads
export const canAddQAComments = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role === 'QA' || isUserAdmin(user);
};

// Researchers, PIs, Scientists, QA, and Admins can reply to comment threads and mark them resolved
export const canReplyQAComments = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role !== 'Viewer';
};

export const canResolveQAComments = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role !== 'Viewer';
};

// Document Download & Export Permissions:
// STRICT: Only Admin and PI (Principal Investigator) have permission to download/export documents.
export const canExportExperiment = (user?: User | null): boolean => {
  if (!user) return false;
  const role = normalizeRole(user);
  return role === 'PI' || isUserAdmin(user);
};

export const canDownloadDocument = (user?: User | null): boolean => canExportExperiment(user);


