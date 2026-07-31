import React, { useState, useEffect } from 'react';
import { Save, CheckCircle2, Loader2 } from 'lucide-react';
import { useAuth } from '../../providers/AuthProvider';
import { authService } from '../../services/auth.service';
import { getUserDisplayName, getUserInitials, getUserRole, getUserDepartment } from '../../utils/userUtils';

interface SettingsViewProps {
  user?: any;
  onSaveUser?: (user: any) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onSaveUser }) => {
  const { user, refetchUser } = useAuth();

  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [role, setRole] = useState<string>('Scientist');
  const [department, setDepartment] = useState<string>('Molecular Biology & Gene Editing');
  
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (user) {
      setName(getUserDisplayName(user));
      setEmail(user.email || '');
      setRole(getUserRole(user));
      setDepartment(getUserDepartment(user));
    }
  }, [user]);

  const initials = getUserInitials(user, name);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await authService.updateProfile({
        department,
        designation: role,
      });
      await refetchUser();
      if (onSaveUser && user) {
        onSaveUser({
          ...user,
          name,
          email,
          role,
          department,
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
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-xl font-bold text-slate-800 tracking-tight">User Profile & Lab Settings</h2>
        <p className="text-xs text-slate-500">Manage user credentials, role-based preferences, and security access keys</p>
      </div>

      {savedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Profile changes updated successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
          <div className="w-16 h-16 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xl shadow-md ring-4 ring-blue-50">
            {initials}
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-base">{name || 'User Profile'}</h3>
            <p className="text-xs text-slate-500">{department}</p>
            <span className="inline-block mt-1 text-[10px] font-bold bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              {role}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 bg-slate-50"
              readOnly
            />
            <span className="text-[10px] text-slate-400 mt-0.5 block">Managed by corporate identity system</span>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 bg-slate-50"
              readOnly
            />
            <span className="text-[10px] text-slate-400 mt-0.5 block">Primary corporate SSO email</span>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Role / Designation</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="Admin">Admin</option>
              <option value="PI">PI (Project Owner / Lab Manager)</option>
              <option value="Researcher">Researcher</option>
              <option value="Bioinformatician">Bioinformatician</option>
              <option value="QA">QA (Quality Assurance)</option>
              <option value="Viewer">Viewer (Read Only)</option>
              <option value="Lab Technician">Lab Technician</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Department</label>
            <input
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

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
            <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
