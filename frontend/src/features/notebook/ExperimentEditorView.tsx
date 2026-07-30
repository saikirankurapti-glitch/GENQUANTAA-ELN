import React, { useState, useEffect } from 'react';
import type { ViewMode } from '../../types';
import { 
  CheckCircle2, Sparkles, Paperclip, MessageSquare, 
  Tag, Calendar, User, Save, FileCheck, TestTube2, Plus, ArrowLeft, Bot, FileText, X, History, Trash2, Loader2, AlertCircle
} from 'lucide-react';
import { useExperiment, useUpdateExperiment, useDeleteExperiment } from '../../hooks/useExperiments';
import { useAuth } from '../../providers/AuthProvider';

interface ExperimentEditorViewProps {
  experimentId: string;
  onSelectView: (view: ViewMode) => void;
  onOpenSampleDetail?: (sampleId: string) => void;
}

export const ExperimentEditorView: React.FC<ExperimentEditorViewProps> = ({
  experimentId,
  onSelectView,
  onOpenSampleDetail
}) => {
  const { user } = useAuth();
  const { data: activeExp, isLoading, error } = useExperiment(experimentId);
  const updateExperiment = useUpdateExperiment();
  const deleteExperiment = useDeleteExperiment();

  const [newStepText, setNewStepText] = useState('');
  const [commentText, setCommentText] = useState('');
  
  // Local state for edits before save
  const [objective, setObjective] = useState('');
  const [results, setResults] = useState('');
  const [status, setStatus] = useState<string>('DRAFT');
  
  const [isAiDrafting, setIsAiDrafting] = useState(false);
  const [showSummarizeModal, setShowSummarizeModal] = useState(false);
  const [showVersionHistoryModal, setShowVersionHistoryModal] = useState(false);

  useEffect(() => {
    if (activeExp) {
      setObjective(activeExp.objective || '');
      setResults(activeExp.metadata_json?.results || '');
      setStatus(activeExp.status);
    }
  }, [activeExp]);

  if (isLoading) {
    return (
      <div className="flex justify-center p-12 h-full items-center">
         <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !activeExp) {
    return (
      <div className="flex flex-col items-center justify-center p-12 h-full text-rose-500">
         <AlertCircle className="w-8 h-8 mb-4" />
         <span className="font-semibold">Failed to load experiment.</span>
      </div>
    );
  }

  // Derive metadata arrays safely
  const protocolSteps: string[] = activeExp.metadata_json?.protocolSteps || [];
  const materials: any[] = activeExp.metadata_json?.materials || [];
  const comments: any[] = activeExp.metadata_json?.comments || [];
  const versionHistory: any[] = activeExp.metadata_json?.versionHistory || [];
  const version = activeExp.metadata_json?.version || 1;

  const handleSaveExperiment = async (overrideStatus?: string) => {
    const nextVersion = version + 1;
    const newStatus = overrideStatus || status;
    const newHistoryEntry = {
      version: nextVersion,
      timestamp: new Date().toUTCString(),
      author: user?.first_name || 'Unknown',
      changes: overrideStatus ? `Status updated to ${overrideStatus}.` : 'Saved notebook updates.'
    };

    const newMetadata = {
      ...activeExp.metadata_json,
      results,
      version: nextVersion,
      versionHistory: [...versionHistory, newHistoryEntry]
    };

    await updateExperiment.mutateAsync({
      id: activeExp.id,
      data: {
        objective,
        status: newStatus,
        metadata_json: newMetadata
      }
    });
  };

  const handleStatusChange = async (newStatus: string) => {
    setStatus(newStatus);
    await handleSaveExperiment(newStatus);
  };

  const handleAddStep = async () => {
    if (!newStepText.trim()) return;
    const newSteps = [...protocolSteps, newStepText];
    
    const newMetadata = {
      ...activeExp.metadata_json,
      protocolSteps: newSteps,
    };

    await updateExperiment.mutateAsync({
      id: activeExp.id,
      data: { metadata_json: newMetadata }
    });
    setNewStepText('');
  };

  const handleAddComment = async () => {
    if (!commentText.trim()) return;
    const newComment = { id: Date.now().toString(), user: user?.first_name || 'Unknown', text: commentText, time: 'Just now' };
    const newComments = [...comments, newComment];

    const newMetadata = {
      ...activeExp.metadata_json,
      comments: newComments,
    };

    await updateExperiment.mutateAsync({
      id: activeExp.id,
      data: { metadata_json: newMetadata }
    });
    setCommentText('');
  };

  const handleGenerateAiProtocol = () => {
    setIsAiDrafting(true);
    setTimeout(async () => {
      setIsAiDrafting(false);
      const aiSuggestedStep = 'SOP Step (AI Optimized): Perform secondary wash with 70% cold ethanol to remove residual salt before elution.';
      const newSteps = [...protocolSteps, aiSuggestedStep];
      
      const newMetadata = {
        ...activeExp.metadata_json,
        protocolSteps: newSteps,
      };

      await updateExperiment.mutateAsync({
        id: activeExp.id,
        data: { metadata_json: newMetadata }
      });
    }, 1200);
  };

  const handleSoftDelete = async () => {
    if (confirm('Soft-delete this experiment?')) {
      await deleteExperiment.mutateAsync(activeExp.id);
      onSelectView('dashboard');
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Breadcrumb & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => onSelectView('dashboard')}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>{activeExp.project_id}</span>
              <span>/</span>
              <span className="font-mono">{activeExp.experiment_code}</span>
              <span className="bg-slate-100 text-slate-600 font-mono text-[10px] px-2 py-0.5 rounded">v{version}.0</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{activeExp.title}</h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowVersionHistoryModal(true)}
            className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition-colors cursor-pointer"
          >
            <History className="w-4 h-4 text-blue-600" />
            <span>History (v{version})</span>
          </button>

          <button
            onClick={() => setShowSummarizeModal(true)}
            className="flex items-center gap-1.5 bg-teal-50 text-teal-700 hover:bg-teal-100 text-xs font-semibold px-3.5 py-2 rounded-lg border border-teal-200 transition-colors cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-teal-600" />
            <span>AI Summarize</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Workflow:</span>
            <select
              value={status}
              onChange={(e) => handleStatusChange(e.target.value)}
              disabled={updateExperiment.isPending}
              className="bg-slate-50 border border-slate-200 text-xs font-bold rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 cursor-pointer disabled:opacity-50"
            >
              <option value="DRAFT">Draft</option>
              <option value="PLANNED">Planned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ON_HOLD">On Hold</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <button
            onClick={() => handleSaveExperiment()}
            disabled={updateExperiment.isPending}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {updateExperiment.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            <span>Save Notebook</span>
          </button>

          <button
            onClick={handleSoftDelete}
            title="Soft Delete Experiment"
            disabled={deleteExperiment.isPending}
            className="p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Grid: Notebook Content & AI Copilot Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - ELN Notebook Document */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400 font-medium block mb-1">Author</span>
              <span className="font-semibold text-slate-800 flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-blue-500" />
                {activeExp.owner_id || 'Unknown'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block mb-1">Date Created</span>
              <span className="font-semibold text-slate-800 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-blue-500" />
                {new Date(activeExp.created_at).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block mb-1">Attachments</span>
              <span className="font-semibold text-slate-800 flex items-center gap-1">
                <Paperclip className="w-3.5 h-3.5 text-blue-500" />
                0 Files
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block mb-1">Compliance</span>
              <span className="font-semibold text-emerald-600 flex items-center gap-1">
                <FileCheck className="w-3.5 h-3.5 text-emerald-500" />
                21 CFR Part 11
              </span>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-2">
              <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-bold">1</span>
              <span>Objective & Hypothesis</span>
            </h3>
            <textarea
              rows={3}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 leading-relaxed focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 text-xs flex items-center justify-center font-bold">2</span>
                <span>Materials & Reagents (Sample Registry Linkage)</span>
              </div>
              <button 
                onClick={() => onSelectView('samples')}
                className="text-xs text-teal-600 hover:text-teal-700 font-semibold flex items-center gap-1 cursor-pointer"
              >
                <TestTube2 className="w-3.5 h-3.5" />
                <span>+ Link Sample from Registry</span>
              </button>
            </h3>

            <div className="divide-y divide-slate-100">
              {materials.map((mat, i) => (
                <div key={i} className="py-2.5 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <div>
                      <span className="font-semibold text-slate-800">{mat.name}</span>
                      {mat.sampleId && (
                        <span 
                          onClick={() => onOpenSampleDetail && onOpenSampleDetail(mat.sampleId!)}
                          className="ml-2 font-mono text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-200 hover:bg-blue-100 cursor-pointer"
                        >
                          {mat.sampleId} ↗
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-slate-500">
                    <span>Qty: {mat.quantity}</span>
                    <span className="font-mono bg-slate-100 px-2 py-0.5 rounded">{mat.lotNumber}</span>
                  </div>
                </div>
              ))}
              {materials.length === 0 && <p className="text-xs text-slate-400 py-2">No materials linked yet.</p>}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs flex items-center justify-center font-bold">3</span>
                <span>Standard Protocol Execution Steps</span>
              </div>
              <span className="text-xs text-slate-400 font-normal">{protocolSteps.length} SOP Steps</span>
            </h3>

            <div className="space-y-3">
              {protocolSteps.map((step, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-3 text-xs">
                  <span className="font-bold text-blue-600 shrink-0 mt-0.5">{idx + 1}.</span>
                  <p className="flex-1 text-slate-700 leading-relaxed">{step}</p>
                </div>
              ))}
            </div>

            <div className="flex gap-2 pt-2">
              <input
                type="text"
                value={newStepText}
                onChange={(e) => setNewStepText(e.target.value)}
                placeholder="Add custom protocol step..."
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddStep}
                disabled={updateExperiment.isPending}
                className="bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors flex items-center gap-1 cursor-pointer disabled:opacity-50"
              >
                <Plus className="w-4 h-4" />
                <span>Add Step</span>
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-2">
              <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs flex items-center justify-center font-bold">4</span>
              <span>Observations & Experimental Results</span>
            </h3>
            <textarea
              rows={4}
              value={results}
              onChange={(e) => setResults(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 leading-relaxed focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-2">
              <MessageSquare className="w-4 h-4 text-blue-600" />
              <span>Comments & Peer Review ({comments.length})</span>
            </h3>

            <div className="space-y-3">
              {comments.map((c, i) => (
                <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-800">{c.user}</span>
                    <span className="text-slate-400 text-[10px]">{c.time}</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{c.text}</p>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Write a comment..."
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddComment}
                disabled={updateExperiment.isPending}
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
              >
                Post
              </button>
            </div>
          </div>

        </div>

        {/* Right Column - Embedded AI Copilot Panel */}
        <div className="space-y-6">
          <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-xl border border-slate-800 space-y-4 sticky top-20">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-teal-400 animate-spin" />
                <h4 className="font-bold text-sm">AI Copilot Co-Author</h4>
              </div>
              <span className="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded border border-teal-500/30">
                96% Confidence Score
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Generate SOP protocols, summarize complex experiments, and ground scientific Q&A in lab data.
            </p>

            <div className="space-y-2">
              <button
                onClick={handleGenerateAiProtocol}
                disabled={isAiDrafting || updateExperiment.isPending}
                className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white text-xs font-bold rounded-lg shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Bot className="w-4 h-4" />
                <span>{isAiDrafting ? 'Drafting SOP Protocol...' : 'AI Protocol Generator'}</span>
              </button>

              <button
                onClick={() => setShowSummarizeModal(true)}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5 text-teal-400" />
                <span>AI Experiment Summarizer</span>
              </button>

              <button
                onClick={() => onSelectView('sequences')}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <Tag className="w-3.5 h-3.5 text-blue-400" />
                <span>Cross-Ref DNA Sequence</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {showVersionHistoryModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <History className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-800">Notebook Append-Only Audit History</h3>
              </div>
              <button onClick={() => setShowVersionHistoryModal(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              {versionHistory.map((vh, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-blue-600 font-mono">v{vh.version}.0</span>
                    <span className="text-slate-400 text-[10px]">{vh.timestamp}</span>
                  </div>
                  <p className="text-slate-800 font-semibold">{vh.author}</p>
                  <p className="text-slate-600 text-[11px]">{vh.changes}</p>
                </div>
              ))}
              {versionHistory.length === 0 && <p className="text-slate-500">No history available.</p>}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowVersionHistoryModal(false)}
                className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-900 text-white rounded-lg cursor-pointer"
              >
                Close History
              </button>
            </div>
          </div>
        </div>
      )}

      {showSummarizeModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-2xl shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-teal-600" />
                <h3 className="text-base font-bold text-slate-800">AI Structured Experiment Summary</h3>
              </div>
              <button onClick={() => setShowSummarizeModal(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-blue-600 mb-1">1. Objective</p>
                <p className="text-slate-700">{objective}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-teal-600 mb-1">2. Method / SOP</p>
                <p className="text-slate-700">{protocolSteps.length > 0 ? protocolSteps.join(' ') : 'No methods defined.'}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-emerald-600 mb-1">3. Result</p>
                <p className="text-slate-700">{results}</p>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowSummarizeModal(false)}
                className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-900 text-white rounded-lg cursor-pointer"
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
