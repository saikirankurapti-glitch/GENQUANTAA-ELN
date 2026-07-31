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
  
  // Public / Shared views accessible to all logged-in users
  if (['dashboard', 'settings', 'notifications', 'login', 'landing'].includes(view)) {
    return true;
  }

  // Admin access: full access to all views
  if (isUserAdmin(user)) {
    return true;
  }

  const role = normalizeRole(user);

  // Viewer: Read-only access to View Dashboard, View Projects, View Experiments
  if (role === 'Viewer') {
    return ['dashboard', 'projects', 'eln'].includes(view);
  }

  // QA: Read-only access to Dashboard, Projects, Experiments, Notebook, Samples, Audit Logs, Reports
  if (role === 'QA') {
    return ['dashboard', 'projects', 'eln', 'samples', 'sample-detail', 'audit', 'reports'].includes(view);
  }

  // Bioinformatician: Dashboard, Projects, Sequence Management, Sample Registry, View Experiments
  if (role === 'Bioinformatician') {
    return [
      'dashboard', 'projects', 'sequences', 'sequence-registry', 'sequence-detail',
      'samples', 'sample-detail', 'eln', 'ai-copilot', 'search', 'reports', 'settings'
    ].includes(view);
  }

  // Lab Technician: Dashboard, Experiments (eln), Samples, Inventory, Settings
  if (role === 'Lab Technician') {
    return ['dashboard', 'eln', 'samples', 'sample-detail', 'inventory', 'settings'].includes(view);
  }

  // Researcher: Dashboard, Assigned Projects, Experiments, Notebook, Samples, Protocols
  if (role === 'Researcher') {
    return [
      'dashboard', 'projects', 'eln', 'samples', 'sample-detail',
      'inventory', 'protocols', 'protocol-detail', 'instruments', 'instrument-detail',
      'sequences', 'sequence-registry', 'sequence-detail', 'ai-copilot', 'search', 'settings'
    ].includes(view);
  }

  // PI (Project Owner): Dashboard, Projects, Experiments, Notebook, Samples, Protocols, Reports
  if (role === 'PI') {
    return [
      'dashboard', 'projects', 'eln', 'samples', 'sample-detail',
      'protocols', 'protocol-detail', 'reports', 'ai-copilot', 'search', 'settings'
    ].includes(view);
  }

  // Default fallback for research users
  return !['admin', 'audit'].includes(view);
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
  return isUserAdmin(user) || role === 'PI' || role === 'Researcher' || role === 'Bioinformatician';
};

export const canEditProjects = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI' || role === 'Researcher' || role === 'Bioinformatician';
};

export const canDeleteProjects = (user?: User | null): boolean => {
  if (!user || !canDelete(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI';
};

export const canCreateExperiment = (user?: User | null): boolean => {
  if (!user || !canCreate(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI' || role === 'Researcher' || role === 'Lab Technician';
};

export const canEditExperiment = (user?: User | null): boolean => {
  if (!user || !canEdit(user)) return false;
  const role = normalizeRole(user);
  return isUserAdmin(user) || role === 'PI' || role === 'Researcher' || role === 'Lab Technician';
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
