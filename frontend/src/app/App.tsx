import React, { useState } from 'react';
import type { ViewMode, UserPersona } from '../types';
import { useAuth } from '../providers/AuthProvider';

// Shared Layout Components (src/components/)
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';

// Feature Modules (src/features/)
import { LandingView } from '../features/landing/LandingView';
import { LoginView } from '../features/auth/LoginView';
import { DashboardView } from '../features/dashboard/DashboardView';
import { ProjectsView } from '../features/projects/ProjectsView';
import { ExperimentEditorView } from '../features/notebook/ExperimentEditorView';
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
import { SequenceViewerView } from '../features/sequences/SequenceViewerView';
import { SettingsView } from '../features/admin/SettingsView';
import { AdminPanelView } from '../features/admin/AdminPanelView';
import { AccessDeniedView } from '../components/views/AccessDeniedView';
import { canViewViewMode } from '../utils/permissions';

// Quick Create Modal
import { Plus, X } from 'lucide-react';

export function App() {
  const { isAuthenticated, user } = useAuth();
  
  // Start on Landing Page if not authenticated
  const [currentView, setCurrentView] = useState<ViewMode>('landing');
  const [loginAuthMode, setLoginAuthMode] = useState<'signin' | 'signup'>('signin');
  const [activePersona, setActivePersona] = useState<UserPersona>('Bench Scientist (Researcher)');

  const [selectedExpId, setSelectedExpId] = useState<string>('EXP-2024-101');
  const [selectedSampleId, setSelectedSampleId] = useState<string>('SMP-001024');
  const [selectedProtocolId, setSelectedProtocolId] = useState<string>('');
  const [selectedInventoryId, setSelectedInventoryId] = useState<string>('');
  const [selectedInstrumentId, setSelectedInstrumentId] = useState<string>('');
  const [selectedSequenceRegistryId, setSelectedSequenceRegistryId] = useState<string>('');

  const [showQuickCreateModal, setShowQuickCreateModal] = useState(false);

  const unreadNotificationsCount = 0;

  // Auth handled globally by AuthProvider, redirect view on auth change
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

  const handleOpenSampleDetail = (sampleId: string) => {
    setSelectedSampleId(sampleId);
    setCurrentView('sample-detail');
  };



  const handleNavigateToLogin = (mode: 'signin' | 'signup' = 'signin') => {
    setLoginAuthMode(mode);
    setCurrentView('login');
  };

  // Dedicated Full Screen Views for Landing & Login
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
      {/* Sidebar Navigation */}
      <Sidebar
        currentView={currentView}
        onSelectView={setCurrentView}
        unreadCount={unreadNotificationsCount}
      />

      {/* Main Workspace Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          currentView={currentView}
          onSelectView={setCurrentView}
          unreadCount={unreadNotificationsCount}
          onOpenQuickCreate={() => setShowQuickCreateModal(true)}
          activePersona={activePersona}
          onSelectPersona={setActivePersona}
        />

        {/* Dynamic Screen Viewport */}
        <main className="flex-1 overflow-y-auto">
          {!isViewAllowed ? (
            <AccessDeniedView onNavigateToDashboard={() => setCurrentView('dashboard')} />
          ) : (
            <>
              {currentView === 'dashboard' && (
            <DashboardView
              onSelectView={setCurrentView}
              onOpenExperiment={handleOpenExperiment}
            />
          )}

          {currentView === 'projects' && (
            <ProjectsView
              onSelectView={setCurrentView}
            />
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
              onSelectSample={(id) => {
                setSelectedSampleId(id);
                setCurrentView('sample-detail');
              }}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'sample-detail' && (
            <SampleDetailView
              sampleId={selectedSampleId}
              onSelectSample={setSelectedSampleId}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'protocols' && (
            <ProtocolRegistryView
              onSelectProtocol={(id) => {
                setSelectedProtocolId(id);
                setCurrentView('protocol-detail');
              }}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'protocol-detail' && (
            <ProtocolDetailView
              protocolId={selectedProtocolId}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'inventory' && (
            <InventoryRegistryView
              onSelectInventoryItem={(id) => {
                setSelectedInventoryId(id);
                setCurrentView('inventory-detail');
              }}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'inventory-detail' && (
            <InventoryDetailView
              inventoryId={selectedInventoryId}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'instruments' && (
            <InstrumentRegistryView
              onSelectInstrument={(id) => {
                setSelectedInstrumentId(id);
                setCurrentView('instrument-detail');
              }}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'instrument-detail' && (
            <InstrumentDetailView
              instrumentId={selectedInstrumentId}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'sequence-registry' && (
            <SequenceRegistryView
              onSelectSequence={(id) => {
                setSelectedSequenceRegistryId(id);
                setCurrentView('sequence-detail');
              }}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'sequence-detail' && (
            <SequenceDetailView
              sequenceId={selectedSequenceRegistryId}
              onSelectView={setCurrentView}
            />
          )}

          {currentView === 'settings' && (
            <SettingsView
              user={user as any} // Cast to any because user type in view diverges from real user
              onSaveUser={() => {}}
            />
          )}

          {currentView === 'admin' && (
            <AdminPanelView
              onSelectView={setCurrentView}
              activePersona={activePersona}
            />
          )}
            </>
          )}
        </main>
      </div>

      {/* Quick Create Entry Modal */}
      {showQuickCreateModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-800">Quick Create Entry</h3>
              <button onClick={() => setShowQuickCreateModal(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500">What research item would you like to create?</p>

            <div className="grid grid-cols-1 gap-3">
              <button
                onClick={() => { setShowQuickCreateModal(false); setCurrentView('eln'); }}
                className="p-3.5 rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 text-left transition-all flex items-center justify-between cursor-pointer"
              >
                <div>
                  <p className="text-xs font-bold text-slate-800">New ELN Experiment</p>
                  <p className="text-[11px] text-slate-500">Draft protocols, hypothesis & observations</p>
                </div>
                <Plus className="w-4 h-4 text-blue-600" />
              </button>

              <button
                onClick={() => { setShowQuickCreateModal(false); setCurrentView('samples'); }}
                className="p-3.5 rounded-xl border border-slate-200 hover:border-teal-500 hover:bg-teal-50/50 text-left transition-all flex items-center justify-between cursor-pointer"
              >
                <div>
                  <p className="text-xs font-bold text-slate-800">Register Sample / Reagent</p>
                  <p className="text-[11px] text-slate-500">Cell lines, plasmids & freezer storage slot</p>
                </div>
                <Plus className="w-4 h-4 text-teal-600" />
              </button>

              <button
                onClick={() => { setShowQuickCreateModal(false); setCurrentView('projects'); }}
                className="p-3.5 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 text-left transition-all flex items-center justify-between cursor-pointer"
              >
                <div>
                  <p className="text-xs font-bold text-slate-800">New Research Workspace</p>
                  <p className="text-[11px] text-slate-500">Create a collaborative project folder</p>
                </div>
                <Plus className="w-4 h-4 text-indigo-600" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
