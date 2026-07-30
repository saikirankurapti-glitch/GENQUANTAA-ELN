import React, { useState } from 'react';
import type { ViewMode, UserPersona } from '../../types';
import { useAuth } from '../../providers/AuthProvider';
import { getUserDisplayName } from '../../utils/userUtils';
import { UserPlus, ShieldAlert, CheckCircle2, UserX, Database, HardDrive } from 'lucide-react';

interface AdminPanelViewProps {
  onSelectView: (view: ViewMode) => void;
  activePersona?: UserPersona;
}

export const AdminPanelView: React.FC<AdminPanelViewProps> = ({ activePersona }) => {
  const { user } = useAuth();
  const currentUserName = getUserDisplayName(user);
  const currentUserEmail = user?.email || 'admin@organization.com';

  const [users, setUsers] = useState([
    { id: 'u1', name: currentUserName, email: currentUserEmail, role: 'Admin', status: 'Active', department: 'Molecular AI & UX' },
    { id: 'u2', name: 'Dr. Sarah Johnson', email: 'sarah.johnson@organization.com', role: 'Scientist', status: 'Active', department: 'Gene Editing' },
    { id: 'u3', name: 'Raj', email: 'raj@organization.com', role: 'Bioinformatician', status: 'Active', department: 'FastAPI Microservices' },
    { id: 'u4', name: 'Sai Kiran', email: 'saikiran@organization.com', role: 'Admin', status: 'Active', department: 'Infrastructure & DB' },
    { id: 'u5', name: 'Ananya', email: 'ananya@organization.com', role: 'QA Auditor', status: 'Active', department: 'Quality Assurance' },
    { id: 'u6', name: 'Ashwin', email: 'ashwin@organization.com', role: 'PI / Manager', status: 'Active', department: 'Bioinformatics' },
  ]);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Scientist');
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const isAdminAccess = activePersona ? activePersona.includes('Admin') : true;

  const handleDeactivate = (userId: string, userName: string) => {
    setUsers(users.map(u => u.id === userId ? { ...u, status: 'Deactivated' } : u));
    setActionSuccessMsg(`Deactivated user ${userName}. Tokens revoked & audit log entry created.`);
    setTimeout(() => setActionSuccessMsg(null), 3500);
  };

  const handleInviteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    const newUser = {
      id: `u-${Date.now()}`,
      name: inviteEmail.split('@')[0],
      email: inviteEmail,
      role: inviteRole,
      status: 'Active',
      department: 'R&D Discovery'
    };

    setUsers([...users, newUser]);
    setShowInviteModal(false);
    setInviteEmail('');
    setActionSuccessMsg(`Invitation sent to ${inviteEmail} with assigned role ${inviteRole}.`);
    setTimeout(() => setActionSuccessMsg(null), 3500);
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Admin Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Admin Panel (Org Settings & User Management)</h2>
          <p className="text-xs text-slate-500">Org-level configuration, role assignment, storage quota, and audit logging</p>
        </div>

        <button 
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <UserPlus className="w-4 h-4" />
          <span>Invite User by Email</span>
        </button>
      </div>

      {actionSuccessMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}

      {/* Org Quota Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] text-slate-400 font-medium uppercase">Storage Quota Used</p>
            <p className="text-sm font-bold text-slate-800">1.2 TB / 5.0 TB (24%)</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] text-slate-400 font-medium uppercase">Active User Licenses</p>
            <p className="text-sm font-bold text-slate-800">{users.filter(u => u.status === 'Active').length} Active Seats</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] text-slate-400 font-medium uppercase">Compliance Policy</p>
            <p className="text-sm font-bold text-slate-800">21 CFR Part 11 Active</p>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Email</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Admin Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-800 flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-[10px]">
                      {u.name.substring(0, 2).toUpperCase()}
                    </div>
                    <span>{u.name}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono">{u.email}</td>
                  <td className="py-3.5 px-4">
                    <span className="bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded text-[10px]">
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600">{u.department}</td>
                  <td className="py-3.5 px-4">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      u.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                    }`}>
                      {u.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    {u.status === 'Active' ? (
                      <button 
                        onClick={() => handleDeactivate(u.id, u.name)}
                        className="text-xs font-semibold text-rose-600 hover:text-rose-700 flex items-center gap-1 justify-end ml-auto cursor-pointer"
                      >
                        <UserX className="w-3.5 h-3.5" />
                        <span>Deactivate</span>
                      </button>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Revoked</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invite User Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">Invite Team Member & Assign Role</h3>
            <form onSubmit={handleInviteSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="collaborator@organization.com"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assign Role (RBAC)</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 cursor-pointer"
                >
                  <option value="Scientist">Scientist (Researcher)</option>
                  <option value="PI / Manager">Lab Manager / PI</option>
                  <option value="Bioinformatician">Bioinformatician</option>
                  <option value="QA Auditor">QA Auditor</option>
                  <option value="Admin">Admin (IT/Ops)</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm cursor-pointer"
                >
                  Send Invitation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
