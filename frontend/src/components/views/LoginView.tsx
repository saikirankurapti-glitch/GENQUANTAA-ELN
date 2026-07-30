import React from 'react';
import { ViewMode } from '../../types';
import { Dna, Lock, ArrowRight, Shield } from 'lucide-react';

interface LoginViewProps {
  onLoginSuccess: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 text-white relative overflow-hidden">
      {/* Glow Effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md bg-slate-800/80 backdrop-blur-xl border border-slate-700 rounded-3xl p-8 shadow-2xl space-y-6 relative z-10">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-teal-400 flex items-center justify-center text-white mx-auto shadow-lg shadow-blue-500/30">
            <Dna className="w-8 h-8 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">AI-Powered ELN</h1>
          <p className="text-xs text-slate-400">Unified Electronic Lab Notebook & Discovery Platform</p>
        </div>

        {/* SSO Buttons */}
        <div className="space-y-3">
          <button
            onClick={onLoginSuccess}
            className="w-full py-3 bg-white hover:bg-slate-100 text-slate-900 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-3 shadow-md"
          >
            <svg className="w-4 h-4" viewBox="0 0 23 23">
              <path fill="#f35325" d="M1 1h10v10H1z"/>
              <path fill="#81bc06" d="M12 1h10v10H12z"/>
              <path fill="#05a6f0" d="M1 12h10v10H1z"/>
              <path fill="#ffba08" d="M12 12h10v10H12z"/>
            </svg>
            <span>Sign in with Microsoft 365</span>
          </button>

          <button
            onClick={onLoginSuccess}
            className="w-full py-3 bg-slate-700/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-600 transition-all flex items-center justify-center gap-3"
          >
            <Shield className="w-4 h-4 text-teal-400" />
            <span>Sign in with Okta SSO</span>
          </button>
        </div>

        <div className="relative flex items-center justify-center my-4">
          <div className="border-t border-slate-700 w-full"></div>
          <span className="bg-slate-800 px-3 text-[10px] text-slate-500 uppercase tracking-widest absolute">or email</span>
        </div>

        {/* Email & Password Demo Form */}
        <form onSubmit={(e) => { e.preventDefault(); onLoginSuccess(); }} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Email</label>
            <input
              type="email"
              placeholder="user@organization.com"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Password</label>
            <input
              type="password"
              defaultValue="••••••••••••"
              className="w-full bg-slate-900/80 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
          >
            <span>Enter ELN Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <p className="text-[10px] text-center text-slate-500">
          21 CFR Part 11 Compliant & TLS 1.3 Encrypted Session
        </p>
      </div>
    </div>
  );
};
