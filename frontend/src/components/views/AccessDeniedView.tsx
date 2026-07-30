import React from 'react';
import { ShieldAlert, ArrowLeft, Lock } from 'lucide-react';

interface AccessDeniedViewProps {
  onNavigateToDashboard: () => void;
}

export const AccessDeniedView: React.FC<AccessDeniedViewProps> = ({ onNavigateToDashboard }) => {
  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6 text-slate-800">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 p-8 shadow-xl text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto shadow-sm">
          <ShieldAlert className="w-8 h-8" />
        </div>
        
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-100 text-rose-800 text-[11px] font-bold uppercase tracking-wider">
            <Lock className="w-3 h-3" />
            <span>403 Forbidden Access</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Access Restricted</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            You do not have the required role permissions to access this menu or admin feature. Please contact your system administrator if you believe this is an error.
          </p>
        </div>

        <button
          onClick={onNavigateToDashboard}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-md transition-colors flex items-center justify-center gap-2 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </button>
      </div>
    </div>
  );
};
