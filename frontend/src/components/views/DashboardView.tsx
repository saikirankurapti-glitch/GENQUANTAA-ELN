import React from 'react';
import { Project, Experiment, Sample, ViewMode } from '../../types';
import { useAuth } from '../../providers/AuthProvider';
import { getUserDisplayName } from '../../utils/userUtils';
import { 
  FolderKanban, FlaskConical, TestTube2, Sparkles, 
  TrendingUp, Clock, CheckCircle2, ArrowRight, Dna, FileText, ChevronRight
} from 'lucide-react';

interface DashboardViewProps {
  projects: Project[];
  experiments: Experiment[];
  samples: Sample[];
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  projects,
  experiments,
  samples,
  onSelectView,
  onOpenExperiment
}) => {
  const { user } = useAuth();
  const activeProjectsCount = projects.filter(p => p.status === 'Active').length;
  const completedExpCount = experiments.filter(e => e.status === 'Completed').length;
  const totalSamples = samples.length;

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-blue-500/30 text-blue-100 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-blue-400/30">
                Welcome back, {getUserDisplayName(user)}
              </span>
            </div>
            <h2 className="text-2xl font-extrabold tracking-tight">AI-Powered Electronic Lab Notebook (ELN)</h2>
            <p className="text-blue-100 text-sm mt-1 max-w-xl">
              Accelerate molecular biology, CRISPR gene editing, and sample tracking with embedded AI protocol generation & RAG discovery.
            </p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => onSelectView('ai-copilot')}
              className="bg-white text-blue-700 hover:bg-blue-50 text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-colors flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Launch AI Copilot</span>
            </button>
            <button 
              onClick={() => onSelectView('eln')}
              className="bg-blue-800/60 hover:bg-blue-800 text-white text-xs font-semibold px-4 py-2.5 rounded-xl border border-blue-400/40 transition-colors flex items-center gap-2"
            >
              <FlaskConical className="w-4 h-4" />
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
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Projects</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{projects.length}</h3>
            <span className="inline-flex items-center text-xs font-medium text-emerald-600 mt-1">
              <TrendingUp className="w-3 h-3 mr-1" />
              {activeProjectsCount} Active Workspaces
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <FolderKanban className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Experiments</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{experiments.length}</h3>
            <span className="inline-flex items-center text-xs font-medium text-blue-600 mt-1">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              {completedExpCount} Completed Entries
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <FlaskConical className="w-6 h-6" />
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Registered Samples</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{totalSamples}</h3>
            <span className="inline-flex items-center text-xs font-medium text-indigo-600 mt-1">
              <TestTube2 className="w-3 h-3 mr-1" />
              Tracked in Cryo Storage
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
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 overflow-x-auto">
            {experiments.map((exp) => (
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
                      <span>ID: {exp.id}</span>
                      <span>Project: {exp.projectName}</span>
                      <span>Author: {exp.author}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="hidden sm:inline">{exp.date}</span>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: AI Insights & Quick Actions Widget */}
        <div className="space-y-6">
          {/* AI Insights Card */}
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
              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <p className="font-semibold text-teal-300 mb-1">CRISPR Efficiency Optimization</p>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  Based on 14 recent transfection runs, increasing Lipofectamine 3000 volume to 7.5 µL raises knockout yield by 12.4%.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <p className="font-semibold text-blue-300 mb-1">Sequence Primer Match</p>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  Primer set GX-F2 matches target sequence Gene X at exon 1 with 100% specificity (TM: 60.5°C).
                </p>
              </div>
            </div>

            <button 
              onClick={() => onSelectView('ai-copilot')}
              className="w-full py-2 bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-600 hover:to-blue-700 text-white font-semibold text-xs rounded-lg transition-all text-center shadow-md shadow-teal-500/20"
            >
              Ask AI Copilot
            </button>
          </div>

          {/* Quick Shortcuts */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <h4 className="font-bold text-sm text-slate-800">Quick Shortcuts</h4>
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={() => onSelectView('sequences')}
                className="p-3 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 text-left transition-all"
              >
                <Dna className="w-5 h-5 text-blue-600 mb-1.5" />
                <p className="text-xs font-semibold text-slate-700">Sequence Viewer</p>
                <p className="text-[10px] text-slate-500">FASTA & BLAST</p>
              </button>
              <button 
                onClick={() => onSelectView('samples')}
                className="p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-teal-50/50 text-left transition-all"
              >
                <TestTube2 className="w-5 h-5 text-teal-600 mb-1.5" />
                <p className="text-xs font-semibold text-slate-700">Sample Registry</p>
                <p className="text-[10px] text-slate-500">Freezer map</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
