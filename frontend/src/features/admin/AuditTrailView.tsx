import React from 'react';
import type { AuditLogItem, ViewMode } from '../../types';
import { ShieldCheck, Download } from 'lucide-react';

interface AuditTrailViewProps {
  logs: AuditLogItem[];
  onSelectView: (view: ViewMode) => void;
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ logs }) => {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">Audit Trail & Activity Logs</h2>
          </div>
          <p className="text-xs text-slate-500">Immutable 21 CFR Part 11 compliant event trail and electronic signatures</p>
        </div>

        <button className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer">
          <Download className="w-4 h-4" />
          <span>Export Compliance Audit Log</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Target Object</th>
                <th className="py-3 px-4">Event Details</th>
                <th className="py-3 px-4">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium font-mono">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 px-4 text-slate-500 text-[11px]">{log.timestamp}</td>
                  <td className="py-3.5 px-4 font-sans font-semibold text-slate-800">{log.user}</td>
                  <td className="py-3.5 px-4">
                    <span className="bg-blue-50 text-blue-700 font-bold px-2 py-0.5 rounded text-[10px]">
                      {log.action}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-slate-700">{log.targetObject}</td>
                  <td className="py-3.5 px-4 font-sans text-slate-600 max-w-xs truncate">{log.details}</td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">{log.ipAddress}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
