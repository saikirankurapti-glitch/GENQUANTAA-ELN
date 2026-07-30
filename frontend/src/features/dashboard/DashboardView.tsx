import React from 'react';
import type { ViewMode } from '../../types';
import { 
  FolderKanban, FlaskConical, TestTube2, Sparkles, 
  TrendingUp, CheckCircle2, ArrowRight, ChevronRight, Loader2, AlertCircle
} from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';

interface DashboardViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onSelectView,
  onOpenExperiment
}) => {
  const { data: dashboardData, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="p-6 h-full flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-4" />
        <p className="text-sm font-semibold text-slate-600">Loading Dashboard Data...</p>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="p-6 h-full flex flex-col items-center justify-center">
        <AlertCircle className="w-8 h-8 text-rose-500 mb-4" />
        <p className="text-sm font-semibold text-rose-600">Failed to load dashboard data.</p>
        <p className="text-xs text-slate-500 mt-2">{error?.message}</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight">AI-Powered Electronic Lab Notebook (ELN)</h2>
            <p className="text-blue-100 text-sm mt-1 max-w-xl">
              Accelerate molecular biology, CRISPR gene editing, and sample tracking with embedded AI protocol generation & RAG discovery.
            </p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => onSelectView('ai-copilot')}
              className="bg-white hover:bg-blue-50 text-blue-700 text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-colors flex items-center gap-2 cursor-pointer border border-white/80"
            >
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Launch AI Copilot</span>
            </button>
            <button 
              onClick={() => onSelectView('eln')}
              className="bg-white hover:bg-blue-50 text-blue-700 text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-colors flex items-center gap-2 cursor-pointer border border-white/80"
            >
              <FlaskConical className="w-4 h-4 text-blue-600" />
              <span>New Experiment</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Projects</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{dashboardData.project_count}</h3>
            <span className="inline-flex items-center text-xs font-medium text-emerald-600 mt-1">
              <TrendingUp className="w-3 h-3 mr-1" />
              Active Workspaces
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <FolderKanban className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Experiments</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{dashboardData.active_experiment_count}</h3>
            <span className="inline-flex items-center text-xs font-medium text-blue-600 mt-1">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              {dashboardData.completed_experiment_count} Completed Entries
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <FlaskConical className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Pending Notifications</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{dashboardData.pending_notifications.length}</h3>
            <span className="inline-flex items-center text-xs font-medium text-indigo-600 mt-1">
              <TestTube2 className="w-3 h-3 mr-1" />
              Review Required
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <TestTube2 className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">AI Copilot Insights</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">3,672</h3>
            <span className="inline-flex items-center text-xs font-medium text-teal-600 mt-1">
              <Sparkles className="w-3 h-3 mr-1" />
              RAG Queries Answered
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Sparkles className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Content Grid: Recent Experiments & AI Insights Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Experiments Table (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-base">Recent ELN Experiments</h3>
              <p className="text-xs text-slate-500">Live feed of active notebook entries and protocol updates</p>
            </div>
            <button 
              onClick={() => onSelectView('eln')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 overflow-x-auto">
            {dashboardData.recent_experiments.map((exp) => (
              <div 
                key={exp.id}
                onClick={() => onOpenExperiment(exp.id)}
                className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                    exp.status === 'Completed' ? 'bg-emerald-50 text-emerald-600' :
                    exp.status === 'In Progress' ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-600'
                  }`}>
                    <FlaskConical className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-800 text-sm group-hover:text-blue-600 transition-colors">
                        {exp.title}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        exp.status === 'Completed' ? 'bg-emerald-100 text-emerald-700' :
                        exp.status === 'In Progress' ? 'bg-blue-100 text-blue-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>
                        {exp.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                      <span>ID: {exp.experiment_number}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="hidden sm:inline">{new Date(exp.updated_at).toLocaleDateString()}</span>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
                </div>
              </div>
            ))}
            {dashboardData.recent_experiments.length === 0 && (
              <div className="p-8 text-center text-slate-500 text-sm">
                No recent experiments found. Create one to get started.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: AI Insights Widget */}
        <div className="space-y-6">
          <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-teal-400 animate-pulse" />
                <h4 className="font-bold text-sm">AI Copilot Recommendations</h4>
              </div>
              <span className="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded border border-teal-500/30 font-mono">
                RAG Engine
              </span>
            </div>

            <div className="space-y-3 text-xs">
              {dashboardData.ai_copilot_shortcuts.map(shortcut => (
                <div key={shortcut.shortcut_id} className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                  <p className="font-semibold text-teal-300 mb-1">{shortcut.title}</p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    {shortcut.suggested_prompt}
                  </p>
                </div>
              ))}
              {dashboardData.ai_copilot_shortcuts.length === 0 && (
                 <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                  <p className="font-semibold text-teal-300 mb-1">CRISPR Efficiency Optimization</p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Based on 14 recent transfection runs, increasing Lipofectamine 3000 volume to 7.5 µL raises knockout yield by 12.4%.
                  </p>
                </div>
              )}
            </div>

            <button 
              onClick={() => onSelectView('ai-copilot')}
              className="w-full py-2 bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-600 hover:to-blue-700 text-white font-semibold text-xs rounded-lg transition-all text-center shadow-md shadow-teal-500/20 cursor-pointer"
            >
              Ask AI Copilot
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
