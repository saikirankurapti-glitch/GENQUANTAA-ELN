import React from 'react';
import { ViewMode } from '../../types';
import { useAuth } from '../../providers/AuthProvider';
import { getUserDisplayName } from '../../utils/userUtils';
import { ShieldCheck, UserPlus, Search, CheckCircle2, Lock } from 'lucide-react';

interface AdminPanelViewProps {
  onSelectView: (view: ViewMode) => void;
}

export const AdminPanelView: React.FC<AdminPanelViewProps> = () => {
  const { user } = useAuth();
  const currentUserName = getUserDisplayName(user);
  const currentUserEmail = user?.email || 'admin@organization.com';

  const users = [
    { name: currentUserName, email: currentUserEmail, role: 'Frontend Lead & UX Designer', status: 'Active', department: 'Molecular AI & UX' },
    { name: 'Dr. Sarah Johnson', email: 'sarah.johnson@organization.com', role: 'Scientist / PI', status: 'Active', department: 'Gene Editing' },
    { name: 'Raj', email: 'raj@organization.com', role: 'AI/ML & Backend Engineer', status: 'Active', department: 'FastAPI Microservices' },
    { name: 'Sai Kiran', email: 'saikiran@organization.com', role: 'Database & DevOps Engineer', status: 'Active', department: 'Infrastructure & DB' },
    { name: 'Ananya', email: 'ananya@organization.com', role: 'QA Engineer', status: 'Active', department: 'Quality Assurance' },
    { name: 'Ashwin', email: 'ashwin@organization.com', role: 'Product Manager', status: 'Active', department: 'Bioinformatics' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Admin Panel (RBAC & User Access)</h2>
          <p className="text-xs text-slate-500">Configure role-based access control, user permissions, and security protocols</p>
        </div>

        <button className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors">
          <UserPlus className="w-4 h-4" />
          <span>Add Team Member</span>
        </button>
      </div>

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
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {users.map((u, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
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
                    <span className="bg-emerald-100 text-emerald-700 font-bold px-2 py-0.5 rounded-full text-[10px]">
                      {u.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button className="text-xs font-semibold text-blue-600 hover:text-blue-700">
                      Manage Role
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
