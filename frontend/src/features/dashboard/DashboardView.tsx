import React from 'react';
import type { ViewMode } from '../../types';
import { 
  FolderKanban, FlaskConical, TestTube2, Sparkles, 
  TrendingUp, CheckCircle2, ArrowRight, ChevronRight, Loader2, AlertCircle,
  Clock, Bell, Plus, ShieldCheck, Activity, Dna, Box, Eye, Lock, Shield
} from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
import { useAuth } from '../../providers/AuthProvider';
import { isStrictlyQA, isStrictlyViewer, canUseAICopilot, canCreateExperiment } from '../../utils/permissions';

interface DashboardViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
  onCreateExperiment?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onSelectView,
  onOpenExperiment,
  onCreateExperiment
}) => {
  const { user } = useAuth();
  const { data: dashboardData, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="p-12 h-full flex flex-col items-center justify-center">
        <Loader2 className="w-9 h-9 animate-spin text-blue-600 mb-4" />
        <p className="text-sm font-semibold text-slate-700">Loading Lab Dashboard...</p>
        <p className="text-xs text-slate-400 mt-1">Aggregating workspace experiments & telemetry</p>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="p-12 h-full flex flex-col items-center justify-center">
        <AlertCircle className="w-10 h-10 text-rose-500 mb-3" />
        <p className="text-base font-semibold text-slate-800">Failed to load dashboard data</p>
        <p className="text-xs text-slate-500 mt-1 max-w-md text-center">{error?.message || 'Please check your connection and try again.'}</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const s = (status || '').toLowerCase().replace(/_/g, ' ');
    if (s.includes('complete') || s.includes('approved')) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    if (s.includes('progress')) {
      return 'bg-blue-50 text-blue-700 border-blue-200';
    }
    if (s.includes('review') || s.includes('submitted')) {
      return 'bg-indigo-50 text-indigo-700 border-indigo-200';
    }
    return 'bg-amber-50 text-amber-700 border-amber-200';
  };

  const formatStatus = (status: string) => {
    if (!status) return 'Draft';
    const clean = status.replace(/^ExperimentStatus\./, '').replace(/_/g, ' ');
    return clean.charAt(0).toUpperCase() + clean.slice(1).toLowerCase();
  };

  const displayName = user?.first_name 
    ? `${user.first_name} ${user.last_name || ''}`.trim()
    : (user?.username || 'Researcher');

  const handleTriggerNewExperiment = () => {
    if (onCreateExperiment) {
      onCreateExperiment();
    } else {
      onSelectView('eln');
    }
  };

  const isQA = isStrictlyQA(user);
  const isViewer = isStrictlyViewer(user);
  const allowAICopilot = canUseAICopilot(user);
  const allowCreateExp = canCreateExperiment(user);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Welcome Banner */}
      <div className={`rounded-2xl p-6 text-white shadow-lg relative overflow-hidden ${
        isViewer
          ? 'bg-gradient-to-r from-slate-900 via-purple-950 to-slate-900 border border-purple-500/30'
          : isQA
          ? 'bg-gradient-to-r from-slate-900 via-amber-950 to-slate-900 border border-amber-500/30'
          : 'bg-gradient-to-r from-blue-700 via-indigo-600 to-blue-800'
      }`}>
        <div className="absolute right-0 top-0 w-96 h-96 bg-white/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-white/20 text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full backdrop-blur-sm uppercase tracking-wider flex items-center gap-1">
                {isViewer ? (
                  <Eye className="w-3 h-3 text-purple-300" />
                ) : isQA ? (
                  <ShieldCheck className="w-3 h-3 text-amber-300" />
                ) : (
                  <Activity className="w-3 h-3 text-cyan-300" />
                )}
                {isViewer ? 'Read-Only Inspection Console' : isQA ? 'QA Compliance Console' : 'R&D Operations Hub'}
              </span>
              <span className="text-blue-200 text-xs">GenQuantaa Cloud v2.4</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome back, {displayName}
            </h2>
            <p className="text-blue-100 text-sm mt-1.5 max-w-2xl leading-relaxed">
              {isViewer
                ? 'You have read-only inspection access across all research notebooks, protocols, and inventory. Creation, edits, AI generation, and exports are restricted.'
                : isQA 
                ? 'Quality Assurance, 21 CFR Part 11 audit trails, and document review verification console.'
                : 'Real-time workspace telemetry, electronic notebook tracking, and AI-accelerated CRISPR protocol intelligence.'
              }
            </p>
          </div>
          <div className="flex flex-wrap gap-2.5">
            {isViewer && (
              <>
                <button 
                  onClick={() => onSelectView('eln')}
                  className="bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer border border-purple-400/40"
                >
                  <FlaskConical className="w-4 h-4 text-white" />
                  <span>Browse Experiments</span>
                </button>
                <button 
                  onClick={() => onSelectView('projects')}
                  className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all flex items-center gap-2 cursor-pointer border border-white/20"
                >
                  <FolderKanban className="w-4 h-4 text-purple-300" />
                  <span>View Projects</span>
                </button>
              </>
            )}
            {!isViewer && allowAICopilot && (
              <button 
                onClick={() => onSelectView('ai-copilot')}
                className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all flex items-center gap-2 cursor-pointer border border-white/25 shadow-sm backdrop-blur-sm"
              >
                <Sparkles className="w-4 h-4 text-cyan-300" />
                <span>AI Copilot</span>
              </button>
            )}
            {!isViewer && allowCreateExp && (
              <button 
                onClick={handleTriggerNewExperiment}
                className="bg-white hover:bg-blue-50 text-blue-800 text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer border border-white"
              >
                <Plus className="w-4 h-4 text-blue-700" />
                <span>New Experiment</span>
              </button>
            )}
            {!isViewer && isQA && (
              <button 
                onClick={() => onSelectView('experiments')}
                className="bg-white hover:bg-amber-50 text-slate-900 text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer border border-white"
              >
                <FlaskConical className="w-4 h-4 text-amber-600" />
                <span>Review Experiments</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Workspaces */}
        <div 
          onClick={() => onSelectView('projects')}
          className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-blue-300 transition-all flex items-center justify-between cursor-pointer group"
        >
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Workspaces</p>
            <h3 className="text-3xl font-extrabold text-slate-800 mt-1 group-hover:text-blue-600 transition-colors">
              {dashboardData.project_count}
            </h3>
            <span className="inline-flex items-center text-xs font-medium text-emerald-600 mt-1">
              <TrendingUp className="w-3.5 h-3.5 mr-1" />
              Active Projects
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <FolderKanban className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 2: Active Experiments */}
        <div 
          onClick={() => onSelectView('eln')}
          className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-teal-300 transition-all flex items-center justify-between cursor-pointer group"
        >
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Experiments</p>
            <h3 className="text-3xl font-extrabold text-slate-800 mt-1 group-hover:text-teal-600 transition-colors">
              {dashboardData.active_experiment_count}
            </h3>
            <span className="inline-flex items-center text-xs font-medium text-blue-600 mt-1">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
              {dashboardData.completed_experiment_count} Completed Entries
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <FlaskConical className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 3: Pending Notifications / Review Required */}
        <div 
          onClick={() => onSelectView('notifications')}
          className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all flex items-center justify-between cursor-pointer group"
        >
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Notifications</p>
            <h3 className="text-3xl font-extrabold text-slate-800 mt-1 group-hover:text-indigo-600 transition-colors">
              {dashboardData.pending_notifications.length}
            </h3>
            <span className="inline-flex items-center text-xs font-medium text-indigo-600 mt-1">
              <TestTube2 className="w-3.5 h-3.5 mr-1" />
              {dashboardData.review_required_count ?? 0} Review Required
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <Bell className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 4: Samples & Storage */}
        <div 
          onClick={() => onSelectView('samples')}
          className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-amber-300 transition-all flex items-center justify-between cursor-pointer group"
        >
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Samples & Registry</p>
            <h3 className="text-3xl font-extrabold text-slate-800 mt-1 group-hover:text-amber-600 transition-colors">
              {dashboardData.total_samples_count ?? 0}
            </h3>
            <span className="inline-flex items-center text-xs font-medium text-amber-600 mt-1">
              <Box className="w-3.5 h-3.5 mr-1" />
              Tracked in Storage
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
            <Dna className="w-6 h-6" />
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
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer transition-colors"
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
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-100 transition-colors">
                    <FlaskConical className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-slate-800 text-sm group-hover:text-blue-600 transition-colors">
                        {exp.title}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusBadge(exp.status)}`}>
                        {formatStatus(exp.status)}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      <span className="font-mono text-slate-500">{exp.experiment_number}</span>
                      <span>•</span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {exp.updated_at ? new Date(exp.updated_at).toLocaleDateString() : 'Recent'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            ))}
            {dashboardData.recent_experiments.length === 0 && (
              <div className="p-12 text-center text-slate-500 text-sm flex flex-col items-center">
                <FlaskConical className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No experiments created yet</p>
                <p className="text-xs text-slate-400 mt-1">Create your first experiment to start recording research data.</p>
                {allowCreateExp && (
                  <button
                    onClick={handleTriggerNewExperiment}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer shadow-sm"
                  >
                    Create Experiment
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: AI Insights, QA Audit Tasks, or Viewer Restrictions */}
        <div className="space-y-6">
          {isViewer ? (
            <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm space-y-4 border border-purple-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-purple-400" />
                  <h4 className="font-bold text-sm">Viewer Access Restrictions</h4>
                </div>
                <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30 font-mono">
                  READ-ONLY
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/80">
                  <p className="font-semibold text-purple-300 mb-0.5 flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5 text-purple-400" />
                    <span>Data Mutations Locked</span>
                  </p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Creating, editing, or deleting experiments, samples, and protocols is disabled for the Viewer role.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/80">
                  <p className="font-semibold text-purple-300 mb-0.5 flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5 text-purple-400" />
                    <span>Document Downloads Locked</span>
                  </p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Full PDF report downloads and document exports are strictly reserved for Admin and PI accounts.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/80">
                  <p className="font-semibold text-purple-300 mb-0.5 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-purple-400" />
                    <span>Read-Only Lab Inspection</span>
                  </p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    You can inspect all experiment records, protocols, sample trees, and inventory items.
                  </p>
                </div>
              </div>

              <button 
                onClick={() => onSelectView('eln')}
                className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs rounded-xl transition-all text-center shadow-md shadow-purple-500/20 cursor-pointer"
              >
                Inspect Experiment Notebooks
              </button>
            </div>
          ) : isQA ? (
            <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm space-y-4 border border-amber-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-amber-400" />
                  <h4 className="font-bold text-sm">QA Compliance Oversight</h4>
                </div>
                <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/30 font-mono">
                  21 CFR PART 11
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div 
                  onClick={() => onSelectView('experiments')}
                  className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/80 hover:border-amber-500/50 hover:bg-slate-800 transition-all cursor-pointer group"
                >
                  <p className="font-semibold text-amber-300 mb-1 group-hover:text-amber-200">Review Experiment Submissions</p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Open experiments in Document Review mode to add inline comments and compliance findings.
                  </p>
                </div>

                <div 
                  onClick={() => onSelectView('audit')}
                  className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/80 hover:border-blue-500/50 hover:bg-slate-800 transition-all cursor-pointer group"
                >
                  <p className="font-semibold text-blue-300 mb-1 group-hover:text-blue-200">Electronic Audit Trail</p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Verify immutable timestamp logs, digital signatures, and user activity records.
                  </p>
                </div>
              </div>

              <button 
                onClick={() => onSelectView('experiments')}
                className="w-full py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs rounded-xl transition-all text-center shadow-md shadow-amber-500/20 cursor-pointer"
              >
                Inspect Experiments
              </button>
            </div>
          ) : (
            /* Researcher / PI: AI Copilot Card */
            allowAICopilot && (
              <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-teal-400 animate-pulse" />
                    <h4 className="font-bold text-sm">AI Copilot Intelligence</h4>
                  </div>
                  <span className="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded border border-teal-500/30 font-mono">
                    RAG Engine
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  {dashboardData.ai_copilot_shortcuts.map(shortcut => (
                    <div 
                      key={shortcut.shortcut_id} 
                      onClick={() => onSelectView('ai-copilot')}
                      className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/80 hover:border-teal-500/50 hover:bg-slate-800 transition-all cursor-pointer group"
                    >
                      <p className="font-semibold text-teal-300 mb-1 group-hover:text-teal-200">{shortcut.title}</p>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {shortcut.suggested_prompt}
                      </p>
                    </div>
                  ))}
                </div>

                <button 
                  onClick={() => onSelectView('ai-copilot')}
                  className="w-full py-2.5 bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-600 hover:to-blue-700 text-white font-semibold text-xs rounded-xl transition-all text-center shadow-md shadow-teal-500/20 cursor-pointer"
                >
                  Ask AI Copilot
                </button>
              </div>
            )
          )}

          {/* Actionable Notifications Box */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-blue-600" />
                <h4 className="font-bold text-slate-800 text-sm">Lab Notifications</h4>
              </div>
              <button
                onClick={() => onSelectView('notifications')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
              >
                <span>View All</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-2.5">
              {dashboardData.pending_notifications.map(n => (
                <div 
                  key={n.id} 
                  onClick={() => onSelectView('notifications')}
                  className="p-3 rounded-lg bg-slate-50 hover:bg-blue-50/50 border border-slate-100 transition-colors flex items-start gap-2.5 text-xs cursor-pointer group"
                >
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                    n.type === 'action_required' ? 'bg-amber-500 animate-pulse' : 'bg-blue-500'
                  }`}></div>
                  <div className="flex-1">
                    <p className="font-semibold text-slate-800 group-hover:text-blue-600 transition-colors">{n.title}</p>
                    <p className="text-slate-500 text-[11px] mt-0.5">{n.message}</p>
                  </div>
                </div>
              ))}
              {dashboardData.pending_notifications.length === 0 && (
                <p className="text-xs text-slate-400 text-center py-3">All clear! No pending review tasks.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
