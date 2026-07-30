import React, { useState } from 'react';
import type { ViewMode, UserPersona } from '../../types';
import { useAuth } from '../../providers/AuthProvider';
import { getUserInitials } from '../../utils/userUtils';
import { Search, Plus, Bell, Sparkles, Command, ChevronDown, UserCheck } from 'lucide-react';

interface HeaderProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
  unreadCount: number;
  onOpenQuickCreate: () => void;
  activePersona: UserPersona;
  onSelectPersona: (persona: UserPersona) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onSelectView,
  unreadCount,
  onOpenQuickCreate,
  activePersona,
  onSelectPersona
}) => {
  const { user } = useAuth();
  const [searchFocused, setSearchFocused] = useState(false);
  const [showPersonaDropdown, setShowPersonaDropdown] = useState(false);

  const personas: UserPersona[] = [
    'Bench Scientist (Researcher)',
    'Lab Manager / PI',
    'Bioinformatician',
    'QA / Compliance Auditor',
    'Admin (IT/Ops)'
  ];

  const getViewTitle = () => {
    switch (currentView) {
      case 'dashboard': return { title: 'Main Dashboard', sub: 'Single-pane overview of active research, project metrics & AI insights' };
      case 'projects': return { title: 'Projects Workspace', sub: 'Top-level container organizing related experiments & research initiatives' };
      case 'eln': return { title: 'Experiment ELN Notebook', sub: 'Structured digital lab notebook with sample links, 21 CFR Part 11 audit & AI co-authoring' };
      case 'samples': return { title: 'Sample Registry', sub: 'Central biological, plasmid, and reagent inventory catalog with experiment linkage' };
      case 'sample-detail': return { title: 'Sample Inventory Detail', sub: 'Freezer storage grid mapping, QR barcode generator & chain-of-custody log' };
      case 'sequences': return { title: 'Sequence Management & Workbench', sub: 'DNA / RNA / Protein FASTA sequence viewer, annotations & BLAST alignment' };
      case 'ai-copilot': return { title: 'AI Research Copilot Chat', sub: 'RAG scientific Q&A, SOP protocol generator & experiment summarization' };
      case 'search': return { title: 'Global RAG Semantic Search', sub: 'Vector-embedding search across experiments, protocols & notebook entries' };
      case 'reports': return { title: 'Reports & Laboratory Analytics', sub: 'Research throughput, protocol success rates & compliance tracking' };
      case 'notifications': return { title: 'Notifications & Collaboration', sub: 'Peer review mentions, protocol approval digests & assignment alerts' };
      case 'settings': return { title: 'User Profile & Settings', sub: 'Manage user credentials, role access, and notification rules' };
      case 'admin': return { title: 'Admin Panel (RBAC)', sub: 'User onboarding, role permissions & organizational settings' };
      case 'integrations': return { title: 'External Integrations', sub: 'Connected cloud storage, LIMS tools, and instrument telemetry' };
      case 'audit': return { title: 'Audit Trail & Activity Logs', sub: '21 CFR Part 11 compliant event log and electronic signatures' };
      case 'files': return { title: 'File Manager Repository', sub: 'Central storage for raw instrument files, FASTQ data, and PDF exports' };
      case 'login': return { title: 'SSO Authentication', sub: 'Enterprise Single Sign-On Portal' };
      default: return { title: 'ELN Workspace', sub: 'AI-Powered Electronic Lab Notebook' };
    }
  };

  const { title, sub } = getViewTitle();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Title & Subtitle */}
      <div>
        <h1 className="text-lg font-bold text-slate-800 tracking-tight">{title}</h1>
        <p className="text-xs text-slate-500 hidden md:block">{sub}</p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-3">
        
        {/* Active Persona Badge & Switcher */}
        <div className="relative hidden md:block">
          <button
            onClick={() => setShowPersonaDropdown(!showPersonaDropdown)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors text-xs font-semibold"
          >
            <UserCheck className="w-3.5 h-3.5 text-blue-600" />
            <span>Persona: {activePersona.split(' ')[0]}</span>
            <ChevronDown className="w-3.5 h-3.5 text-blue-500" />
          </button>

          {showPersonaDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-30 space-y-1">
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Switch Active User Persona</div>
              {personas.map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    onSelectPersona(p);
                    setShowPersonaDropdown(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs transition-colors flex items-center justify-between ${
                    activePersona === p ? 'bg-blue-50 text-blue-700 font-bold' : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <span>{p}</span>
                  {activePersona === p && <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Global RAG Search Bar Trigger */}
        <div 
          onClick={() => onSelectView('search')}
          className={`relative flex items-center cursor-pointer transition-all ${
            searchFocused ? 'w-72 ring-2 ring-blue-500' : 'w-56'
          }`}
        >
          <Search className="w-4 h-4 text-slate-400 absolute left-3" />
          <input
            type="text"
            readOnly
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            placeholder="Search experiments, samples, DNA..."
            className="w-full bg-slate-100 text-slate-700 text-xs pl-9 pr-12 py-2 rounded-lg border border-slate-200 focus:outline-none cursor-pointer"
          />
          <div className="absolute right-2 flex items-center gap-0.5 bg-slate-200 text-slate-500 px-1.5 py-0.5 rounded text-[10px] font-mono">
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </div>
        </div>

        {/* AI Copilot Status Pill */}
        <button 
          onClick={() => onSelectView('ai-copilot')}
          className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-100 transition-colors text-xs font-medium"
        >
          <Sparkles className="w-3.5 h-3.5 text-teal-600 animate-spin" />
          <span>AI Copilot</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
        </button>

        {/* Quick Add Button */}
        <button
          onClick={onOpenQuickCreate}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Entry</span>
        </button>

        {/* Notification Bell */}
        <button 
          onClick={() => onSelectView('notifications')}
          className="relative p-2 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-white"></span>
          )}
        </button>

        {/* Profile Avatar Pill */}
        <div 
          onClick={() => onSelectView('settings')}
          className="flex items-center gap-2 pl-2 border-l border-slate-200 cursor-pointer hover:opacity-80 transition-opacity"
        >
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs">
            {getUserInitials(user)}
          </div>
        </div>
      </div>
    </header>
  );
};
