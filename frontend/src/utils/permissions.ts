import { User } from '../types/auth';
import { ViewMode } from '../types';
import { getUserRole } from './userUtils';

export type RoleName = 'Admin' | 'Scientist' | 'Lab Technician' | 'Bioinformatician' | 'PI / Manager';

export const isUserAdmin = (user?: User | null): boolean => {
  if (!user) return false;
  const role = getUserRole(user).toLowerCase();
  return role.includes('admin') || role.includes('super');
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

  // Admin-only views blocked for non-admins
  if (['admin', 'audit'].includes(view)) {
    return false;
  }

  const role = getUserRole(user).trim();

  // Lab Technician: Dashboard, Experiments (eln), Samples, Inventory, Settings
  if (role === 'Lab Technician') {
    return ['dashboard', 'eln', 'samples', 'sample-detail', 'inventory', 'settings'].includes(view);
  }

  // Bioinformatician: Dashboard, Projects, Sequence Management, Analysis (ai-copilot, search, reports), Settings
  if (role === 'Bioinformatician') {
    return [
      'dashboard', 'projects', 'sequences', 'sequence-registry', 'sequence-detail',
      'ai-copilot', 'search', 'reports', 'settings'
    ].includes(view);
  }

  // PI / Manager: Dashboard, Projects, Experiments, Samples, Protocols, Reports, Settings
  if (role === 'PI / Manager') {
    return [
      'dashboard', 'projects', 'eln', 'samples', 'sample-detail',
      'protocols', 'protocol-detail', 'reports', 'ai-copilot', 'search', 'settings'
    ].includes(view);
  }

  // Scientist: Dashboard, Projects, Experiments, Sample Registry, Inventory, Protocols, Instruments, Sequence Management, Settings
  if (role === 'Scientist') {
    return [
      'dashboard', 'projects', 'eln', 'samples', 'sample-detail',
      'inventory', 'protocols', 'protocol-detail', 'instruments', 'instrument-detail',
      'sequences', 'sequence-registry', 'sequence-detail', 'ai-copilot', 'search', 'settings'
    ].includes(view);
  }

  // Default fallback for research users
  return !['admin', 'audit'].includes(view);
};

export const canManageUsers = (user?: User | null): boolean => isUserAdmin(user);
export const canManageRoles = (user?: User | null): boolean => isUserAdmin(user);
export const canViewAuditLogs = (user?: User | null): boolean => isUserAdmin(user);
export const canAccessAdminPanel = (user?: User | null): boolean => isUserAdmin(user);

export const canManageProjects = (user?: User | null): boolean => {
  if (!user) return false;
  const role = getUserRole(user);
  return isUserAdmin(user) || role === 'Scientist' || role === 'PI / Manager' || role === 'Bioinformatician';
};

export const canCreateExperiments = (user?: User | null): boolean => {
  if (!user) return false;
  const role = getUserRole(user);
  return isUserAdmin(user) || role === 'Scientist' || role === 'Lab Technician' || role === 'PI / Manager';
};

export const canDeleteProjects = (user?: User | null): boolean => {
  if (!user) return false;
  const role = getUserRole(user);
  return isUserAdmin(user) || role === 'PI / Manager';
};
