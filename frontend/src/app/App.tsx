import React, { useState } from 'react';
import type { ViewMode, UserPersona } from '../types';
import { useAuth } from '../providers/AuthProvider';

// Shared Layout Components
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';

// Feature Modules
import { LandingView } from '../features/landing/LandingView';
import { LoginView } from '../features/auth/LoginView';
import { DashboardView } from '../features/dashboard/DashboardView';
import { ProjectsView } from '../features/projects/ProjectsView';
import { ProjectDetailView } from '../features/projects/ProjectDetailView';
import { ExperimentEditorView } from '../features/notebook/ExperimentEditorView';
import { ExperimentsListView } from '../features/notebook/ExperimentsListView';
import { SampleRegistryView } from '../features/samples/SampleRegistryView';
import { SampleDetailView } from '../features/samples/SampleDetailView';
import { ProtocolRegistryView } from '../features/protocols/ProtocolRegistryView';
import { ProtocolDetailView } from '../features/protocols/ProtocolDetailView';
import { InventoryRegistryView } from '../features/inventory/InventoryRegistryView';
import { InventoryDetailView } from '../features/inventory/InventoryDetailView';
import { InstrumentRegistryView } from '../features/instruments/InstrumentRegistryView';
import { InstrumentDetailView } from '../features/instruments/InstrumentDetailView';
import { SequenceRegistryView } from '../features/sequences/SequenceRegistryView';
import { SequenceDetailView } from '../features/sequences/SequenceDetailView';
import { SettingsView } from '../features/admin/SettingsView';
import { AdminPanelView } from '../features/admin/AdminPanelView';
import { AICopilotChatView } from '../features/ai-copilot/AICopilotChatView';
import { AccessDeniedView } from '../components/views/AccessDeniedView';
import { canViewViewMode } from '../utils/permissions';
import { useCreateExperiment } from '../hooks/useExperiments';

// Icons
import { Plus, X, FlaskConical, TestTube2, FolderOpen, Loader2, AlertCircle, Sparkles } from 'lucide-react';

export function App() {
  const { isAuthenticated, user } = useAuth();

  const [currentView, setCurrentView] = useState<ViewMode>('landing');
  const [loginAuthMode, setLoginAuthMode] = useState<'signin' | 'signup'>('signin');
  const [activePersona, setActivePersona] = useState<UserPersona>('Bench Scientist (Researcher)');

  const [selectedExpId, setSelectedExpId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('SMP-001024');
  const [selectedProtocolId, setSelectedProtocolId] = useState<string>('');
  const [selectedInventoryId, setSelectedInventoryId] = useState<string>('');
  const [selectedInstrumentId, setSelectedInstrumentId] = useState<string>('');
  const [selectedSequenceRegistryId, setSelectedSequenceRegistryId] = useState<string>('');

  // Modal state
  const [showQuickCreateModal, setShowQuickCreateModal] = useState(false);
  const [createStep, setCreateStep] = useState<'choose' | 'experiment'>('choose');

  // New Experiment Form
  const [newExpTitle, setNewExpTitle] = useState('');
  const [newExpCode, setNewExpCode] = useState('');
  const [newExpObjective, setNewExpObjective] = useState('');
  const [newExpPriority, setNewExpPriority] = useState('MEDIUM');
  const [createError, setCreateError] = useState('');

  const createExperiment = useCreateExperiment();
  const unreadNotificationsCount = 0;

  React.useEffect(() => {
    if (isAuthenticated && (currentView === 'landing' || currentView === 'login')) {
      setCurrentView('dashboard');
    }
  }, [isAuthenticated, currentView]);

  const isViewAllowed = canViewViewMode(user, currentView);

  React.useEffect(() => {
    if (isAuthenticated && user && !isViewAllowed) {
      setCurrentView('dashboard');
    }
  }, [isAuthenticated, user, isViewAllowed]);

  const handleOpenExperiment = (expId: string) => {
    setSelectedExpId(expId);
    setCurrentView('eln');
  };

  const handleOpenProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    setCurrentView('project_detail');
  };

  const handleOpenSampleDetail = (sampleId: string) => {
    setSelectedSampleId(sampleId);
    setCurrentView('sample-detail');
  };

  const handleNavigateToLogin = (mode: 'signin' | 'signup' = 'signin') => {
    setLoginAuthMode(mode);
    setCurrentView('login');
  };

  const handleOpenQuickCreate = () => {
    setCreateStep('choose');
    setNewExpTitle('');
    setNewExpCode(`EXP-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 900) + 100)}`);
    setNewExpObjective('');
    setNewExpPriority('MEDIUM');
    setCreateError('');
    setShowQuickCreateModal(true);
  };

  const handleCreateExperiment = async () => {
    if (!newExpTitle.trim()) { setCreateError('Experiment title is required.'); return; }
    if (!newExpCode.trim()) { setCreateError('Experiment code is required.'); return; }
    setCreateError('');
    try {
      const payload: any = {
        title: newExpTitle.trim(),
        experiment_code: newExpCode.trim(),
        priority: newExpPriority,
        status: 'draft',
      };
      if (newExpObjective.trim()) payload.objective = newExpObjective.trim();

      const newExp = await createExperiment.mutateAsync(payload);
      setShowQuickCreateModal(false);
      setSelectedExpId((newExp as any).id || (newExp as any).experiment_code || newExpCode);
      setCurrentView('eln');
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join(', ')
        : typeof detail === 'string' ? detail : 'Failed to create experiment. Please try again.';
      setCreateError(msg);
    }
  };



  if (currentView === 'landing') {
    return (
      <LandingView
        onNavigateToLogin={handleNavigateToLogin}
        onNavigateToDashboard={() => setCurrentView('dashboard')}
      />
    );
  }

  if (currentView === 'login') {
    return (
      <LoginView
        initialMode={loginAuthMode}
        onNavigateToLanding={() => setCurrentView('landing')}
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <LandingView
        onNavigateToLogin={handleNavigateToLogin}
        onNavigateToDashboard={() => setCurrentView('dashboard')}
      />
    );
  }

  return (
    <div className="flex h-screen bg-[#F8FAFC] overflow-hidden text-slate-800 font-sans">
      <Sidebar currentView={currentView} onSelectView={setCurrentView} unreadCount={unreadNotificationsCount} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          currentView={currentView}
          onSelectView={setCurrentView}
          unreadCount={unreadNotificationsCount}
          onOpenQuickCreate={handleOpenQuickCreate}
        />

        <main className="flex-1 overflow-y-auto">
          {!isViewAllowed ? (
            <AccessDeniedView onNavigateToDashboard={() => setCurrentView('dashboard')} />
          ) : (
            <>
              {currentView === 'dashboard' && (
                <DashboardView onSelectView={setCurrentView} onOpenExperiment={handleOpenExperiment} />
              )}
              {currentView === 'projects' && <ProjectsView onSelectView={setCurrentView} onOpenProject={handleOpenProject} />}
              {currentView === 'project_detail' && selectedProjectId && (
                <ProjectDetailView projectId={selectedProjectId} onSelectView={setCurrentView} onOpenExperiment={handleOpenExperiment} />
              )}
              {currentView === 'experiments' && (
                <ExperimentsListView onSelectView={setCurrentView} onOpenExperiment={handleOpenExperiment} />
              )}
              {currentView === 'eln' && (
                <ExperimentEditorView
                  experimentId={selectedExpId}
                  onSelectView={setCurrentView}
                  onOpenSampleDetail={handleOpenSampleDetail}
                />
              )}
              {currentView === 'samples' && (
                <SampleRegistryView
                  onSelectSample={(id) => { setSelectedSampleId(id); setCurrentView('sample-detail'); }}
                  onSelectView={setCurrentView}
                />
              )}
              {currentView === 'sample-detail' && (
                <SampleDetailView sampleId={selectedSampleId} onSelectSample={setSelectedSampleId} onSelectView={setCurrentView} />
              )}
              {currentView === 'protocols' && (
                <ProtocolRegistryView
                  onSelectProtocol={(id) => { setSelectedProtocolId(id); setCurrentView('protocol-detail'); }}
                  onSelectView={setCurrentView}
                />
              )}
              {currentView === 'protocol-detail' && (
                <ProtocolDetailView protocolId={selectedProtocolId} onSelectView={setCurrentView} />
              )}
              {currentView === 'inventory' && (
                <InventoryRegistryView
                  onSelectInventoryItem={(id) => { setSelectedInventoryId(id); setCurrentView('inventory-detail'); }}
                  onSelectView={setCurrentView}
                />
              )}
              {currentView === 'inventory-detail' && (
                <InventoryDetailView inventoryId={selectedInventoryId} onSelectView={setCurrentView} />
              )}
              {currentView === 'instruments' && (
                <InstrumentRegistryView
                  onSelectInstrument={(id) => { setSelectedInstrumentId(id); setCurrentView('instrument-detail'); }}
                  onSelectView={setCurrentView}
                />
              )}
              {currentView === 'instrument-detail' && (
                <InstrumentDetailView instrumentId={selectedInstrumentId} onSelectView={setCurrentView} />
              )}
              {currentView === 'sequence-registry' && (
                <SequenceRegistryView
                  onSelectSequence={(id) => { setSelectedSequenceRegistryId(id); setCurrentView('sequence-detail'); }}
                  onSelectView={setCurrentView}
                />
              )}
              {currentView === 'sequence-detail' && (
                <SequenceDetailView sequenceId={selectedSequenceRegistryId} onSelectView={setCurrentView} />
              )}
              {currentView === 'settings' && <SettingsView user={user as any} onSaveUser={() => {}} />}
              {currentView === 'admin' && <AdminPanelView onSelectView={setCurrentView} />}
              {currentView === 'ai-copilot' && <AICopilotChatView onSelectView={setCurrentView} />}
            </>
          )}
        </main>
      </div>

      {/* ── Create / Quick Create Modal ── */}
      {showQuickCreateModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">

            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                {createStep === 'experiment'
                  ? <FlaskConical className="w-5 h-5 text-blue-600" />
                  : <Plus className="w-5 h-5 text-slate-700" />
                }
                <h3 className="text-base font-bold text-slate-800">
                  {createStep === 'experiment' ? 'New ELN Experiment' : 'Quick Create'}
                </h3>
              </div>
              <button
                onClick={() => setShowQuickCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Step 1: Choose type */}
            {createStep === 'choose' && (
              <div className="p-6 space-y-3">
                <p className="text-xs text-slate-500 mb-4">What research item would you like to create?</p>

                <button
                  onClick={() => setCreateStep('experiment')}
                  className="w-full p-4 rounded-xl border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 text-left transition-all flex items-center gap-3 cursor-pointer group"
                >
                  <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                    <FlaskConical className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-slate-800">New ELN Experiment</p>
                    <p className="text-[11px] text-slate-500">Draft protocols, hypothesis & observations</p>
                  </div>
                  <Plus className="w-4 h-4 text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>

                <button
                  onClick={() => { setShowQuickCreateModal(false); setCurrentView('samples'); }}
                  className="w-full p-4 rounded-xl border border-slate-200 hover:border-teal-400 hover:bg-teal-50/50 text-left transition-all flex items-center gap-3 cursor-pointer group"
                >
                  <div className="w-9 h-9 rounded-lg bg-teal-100 flex items-center justify-center group-hover:bg-teal-200 transition-colors">
                    <TestTube2 className="w-4 h-4 text-teal-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-slate-800">Register Sample / Reagent</p>
                    <p className="text-[11px] text-slate-500">Cell lines, plasmids & freezer storage slot</p>
                  </div>
                  <Plus className="w-4 h-4 text-teal-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>

                <button
                  onClick={() => { setShowQuickCreateModal(false); setCurrentView('projects'); }}
                  className="w-full p-4 rounded-xl border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/50 text-left transition-all flex items-center gap-3 cursor-pointer group"
                >
                  <div className="w-9 h-9 rounded-lg bg-indigo-100 flex items-center justify-center group-hover:bg-indigo-200 transition-colors">
                    <FolderOpen className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-slate-800">New Research Workspace</p>
                    <p className="text-[11px] text-slate-500">Create a collaborative project folder</p>
                  </div>
                  <Plus className="w-4 h-4 text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </div>
            )}

            {/* Step 2: Create Experiment Form */}
            {createStep === 'experiment' && (
              <div className="p-6 space-y-4">
                {/* Title */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Experiment Title <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newExpTitle}
                    onChange={(e) => setNewExpTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreateExperiment()}
                    placeholder="e.g. CRISPR Transfection Protocol HEK293T"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none placeholder-slate-400"
                    autoFocus
                  />
                </div>

                {/* Code */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Experiment Code <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newExpCode}
                    onChange={(e) => setNewExpCode(e.target.value)}
                    placeholder="e.g. EXP-2026-042"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none placeholder-slate-400"
                  />
                </div>

                {/* Objective */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Objective / Hypothesis <span className="text-slate-400 font-normal">(optional — AI can fill this)</span>
                  </label>
                  <textarea
                    rows={3}
                    value={newExpObjective}
                    onChange={(e) => setNewExpObjective(e.target.value)}
                    placeholder="Brief scientific objective... or leave blank and use ⚡ AI Fill All after creation"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none placeholder-slate-400 resize-none"
                  />
                </div>

                {/* Priority */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700">Priority</label>
                  <div className="flex gap-2">
                    {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => (
                      <button
                        key={p}
                        onClick={() => setNewExpPriority(p)}
                        className={`flex-1 py-1.5 rounded-lg text-[11px] font-bold border transition-all cursor-pointer ${
                          newExpPriority === p
                            ? p === 'CRITICAL' ? 'bg-rose-600 text-white border-rose-600'
                              : p === 'HIGH' ? 'bg-orange-500 text-white border-orange-500'
                              : p === 'MEDIUM' ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-slate-600 text-white border-slate-600'
                            : 'bg-white text-slate-500 border-slate-200 hover:border-slate-400'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>

                {/* AI hint */}
                <div className="flex items-start gap-2 bg-violet-50 border border-violet-100 rounded-lg px-3 py-2">
                  <Sparkles className="w-3.5 h-3.5 text-violet-500 mt-0.5 shrink-0" />
                  <p className="text-[11px] text-violet-700 leading-relaxed">
                    After creation, use <strong>⚡ AI Fill All</strong> to auto-generate objective, protocol steps, materials, and results instantly with Groq AI.
                  </p>
                </div>

                {/* Error */}
                {createError && (
                  <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2 text-xs text-rose-700">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    {createError}
                  </div>
                )}

                {/* Buttons */}
                <div className="flex gap-3 pt-1">
                  <button
                    onClick={() => setCreateStep('choose')}
                    className="px-4 py-2.5 rounded-lg border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
                  >
                    ← Back
                  </button>
                  <button
                    onClick={handleCreateExperiment}
                    disabled={createExperiment.isPending || !newExpTitle.trim()}
                    className="flex-1 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-sm"
                  >
                    {createExperiment.isPending
                      ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</>
                      : <><FlaskConical className="w-4 h-4" /> Create & Open Experiment</>
                    }
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
