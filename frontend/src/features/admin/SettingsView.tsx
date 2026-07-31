import React, { useState, useEffect } from 'react';
import { Save, CheckCircle2, Loader2, Lock, ShieldCheck, User as UserIcon, Phone, Building, Key, Bell, Palette, Globe } from 'lucide-react';
import { useAuth } from '../../providers/AuthProvider';
import { authService } from '../../services/auth.service';
import { getUserDisplayName, getUserInitials, getUserRole, getUserDepartment } from '../../utils/userUtils';

interface SettingsViewProps {
  user?: any;
  onSaveUser?: (user: any) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onSaveUser }) => {
  const { user, refetchUser } = useAuth();

  const [displayName, setDisplayName] = useState<string>('');
  const [department, setDepartment] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [theme, setTheme] = useState<string>('light');
  const [language, setLanguage] = useState<string>('en');
  const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(true);
  
  // Password change fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<string | null>(null);

  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (user) {
      setDisplayName(getUserDisplayName(user));
      setDepartment(getUserDepartment(user));
      setPhone(user.phone_number || '');
    }
  }, [user]);

  const initials = getUserInitials(user, displayName);
  const role = getUserRole(user);
  const organizationName = (user as any)?.organization_name || 'Enterprise R&D Discovery Org';
  const tenantName = (user as any)?.tenant_name || 'Default Master Tenant Scope';

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await authService.updateProfile({
        department,
      });
      await refetchUser();
      if (onSaveUser && user) {
        onSaveUser({
          ...user,
          display_name: displayName,
          department,
          phone_number: phone,
        });
      }
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to update profile:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Personal Account & Preferences</h2>
          <p className="text-xs text-slate-500">Manage personal contact details, notifications, password, and UI theme</p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-semibold border border-blue-200">
          <ShieldCheck className="w-4 h-4 text-blue-600" />
          <span>Role: {role}</span>
        </div>
      </div>

      {savedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Profile updated successfully!</span>
        </div>
      )}

      {/* Main Settings Form */}
      <form onSubmit={handleSaveProfile} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
        {/* User Card */}
        <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
          <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-blue-600 to-teal-500 text-white font-bold flex items-center justify-center text-xl shadow-md ring-4 ring-blue-50">
            {initials}
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-base">{displayName || 'User Profile'}</h3>
            <p className="text-xs text-slate-500">{user?.email}</p>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full border border-blue-200">
                Role: {role}
              </span>
              <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200 flex items-center gap-1">
                <Lock className="w-3 h-3 text-slate-400" /> Managed by Admin
              </span>
            </div>
          </div>
        </div>

        {/* Section 1: Read-Only System Security Boundaries */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-slate-400" /> Security Access Boundaries (Read-Only)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-600 mb-1">System Role (Assigned RBAC)</label>
              <input
                type="text"
                disabled
                value={role}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs bg-slate-100 text-slate-600 font-medium cursor-not-allowed"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">Role management is restricted strictly to System Administrators in the Admin Panel</span>
            </div>

            <div>
              <label className="block font-semibold text-slate-600 mb-1">Assigned Organization</label>
              <input
                type="text"
                disabled
                value={organizationName}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs bg-slate-100 text-slate-600 font-medium cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-600 mb-1">Multi-Tenant Workspace Scope</label>
              <input
                type="text"
                disabled
                value={tenantName}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs bg-slate-100 text-slate-600 font-medium cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-600 mb-1">Primary Email (SSO Identity)</label>
              <input
                type="text"
                disabled
                value={user?.email || ''}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs bg-slate-100 text-slate-600 font-medium cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        <hr className="border-slate-100" />

        {/* Section 2: Editable Personal Attributes */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <UserIcon className="w-3.5 h-3.5 text-blue-600" /> Personal Contact & Work Details
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Display Name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Dr. Jane Doe"
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Department</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="Molecular Discovery & AI"
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Contact Phone (E.164)</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555-0199"
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <hr className="border-slate-100" />

        {/* Section 3: Preferences (Theme, Language, Notifications) */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Palette className="w-3.5 h-3.5 text-teal-600" /> User Interface & Regional Preferences
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">UI Theme</label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 cursor-pointer"
              >
                <option value="light">Light Slate (Default)</option>
                <option value="dark">Dark Obsidian</option>
                <option value="system">System Preference</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Preferred Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 cursor-pointer"
              >
                <option value="en">English (US)</option>
                <option value="en-GB">English (UK)</option>
                <option value="de">German (Deutsch)</option>
                <option value="fr">French (Français)</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Notifications</label>
              <div className="pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notificationsEnabled}
                    onChange={(e) => setNotificationsEnabled(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                  />
                  <span className="text-xs text-slate-700">Enable Email Digests & Peer Reviews</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            <span>{isSaving ? 'Saving...' : 'Save Profile Changes'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
