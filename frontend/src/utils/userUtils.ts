import { User } from '../types/auth';

export const getUserDisplayName = (user?: User | null): string => {
  if (!user) return 'User';
  if (user.display_name && user.display_name.trim()) return user.display_name.trim();
  const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim();
  if (fullName) return fullName;
  return user.username || user.email || 'User';
};

export const getUserInitials = (user?: User | null, defaultName?: string): string => {
  const name = user ? getUserDisplayName(user) : (defaultName || 'User');
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  if (parts.length === 1 && parts[0].length > 0) {
    return parts[0].substring(0, Math.min(2, parts[0].length)).toUpperCase();
  }
  return 'U';
};

export const getUserRole = (user?: User | null): string => {
  if (!user) return 'Researcher';
  if (user.roles && user.roles.length > 0 && user.roles[0].role_name) {
    return user.roles[0].role_name;
  }
  if (user.profile?.designation) {
    return user.profile.designation;
  }
  return 'Researcher';
};

export const getUserDepartment = (user?: User | null): string => {
  if (!user) return 'Molecular Biology & Gene Editing';
  if (user.profile?.department) return user.profile.department;
  return 'Molecular Biology & Gene Editing';
};
