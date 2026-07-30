import React, { useState } from 'react';
import type { Experiment, Sample, ViewMode } from '../../types';
import { 
  FlaskConical, CheckCircle2, Sparkles, Paperclip, MessageSquare, 
  Tag, Calendar, User, Save, FileCheck, TestTube2, Plus, ArrowLeft, Bot, FileText, X
} from 'lucide-react';

interface ExperimentEditorViewProps {
  experiment: Experiment;
  samples: Sample[];
  onSaveExperiment: (updated: Experiment) => void;
  onSelectView: (view: ViewMode) => void;
  onOpenSampleDetail?: (sampleId: string) => void;
}

export const ExperimentEditorView: React.FC<ExperimentEditorViewProps> = ({
  experiment,
  samples,
  onSaveExperiment,
  onSelectView,
  onOpenSampleDetail
}) => {
  const [activeExp, setActiveExp] = useState<Experiment>(experiment);
  const [newStepText, setNewStepText] = useState('');
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState<{ id: string; user: string; text: string; time: string }[]>([
    { id: 'c1', user: 'Dr. Sarah Johnson', text: 'Checked out lane 4 on the gel photo. Band density matches predicted 84% knockout.', time: 'May 16, 10:14 AM' },
    { id: 'c2', user: 'Lead Researcher', text: 'Updated material lot numbers and cross-linked sample SMP-001024.', time: 'May 16, 11:30 AM' }
  ]);
  
  const [isAiDrafting, setIsAiDrafting] = useState(false);
  const [showSummarizeModal, setShowSummarizeModal] = useState(false);

  const handleStatusChange = (newStatus: Experiment['status']) => {
    const updated = { ...activeExp, status: newStatus };
    setActiveExp(updated);
    onSaveExperiment(updated);
  };

  const handleAddStep = () => {
    if (!newStepText.trim()) return;
    const updated = {
      ...activeExp,
      protocolSteps: [...activeExp.protocolSteps, newStepText]
    };
    setActiveExp(updated);
    setNewStepText('');
    onSaveExperiment(updated);
  };

  const handleAddComment = () => {
    if (!commentText.trim()) return;
    setComments([
      ...comments,
      { id: Date.now().toString(), user: 'Lead Researcher', text: commentText, time: 'Just now' }
    ]);
    setCommentText('');
  };

  const handleGenerateAiProtocol = () => {
    setIsAiDrafting(true);

    setTimeout(() => {
      setIsAiDrafting(false);
      const aiSuggestedStep = 'SOP Step 6 (AI Optimized): Perform secondary wash with 70% cold ethanol to remove residual salt before elution.';
      setActiveExp(prev => ({
        ...prev,
        protocolSteps: [...prev.protocolSteps, aiSuggestedStep]
      }));
    }, 1200);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Breadcrumb & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => onSelectView('dashboard')}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>{activeExp.projectName}</span>
              <span>/</span>
              <span className="font-mono">{activeExp.id}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{activeExp.title}</h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSummarizeModal(true)}
            className="flex items-center gap-1.5 bg-teal-50 text-teal-700 hover:bg-teal-100 text-xs font-semibold px-3.5 py-2 rounded-lg border border-teal-200 transition-colors"
          >
            <Sparkles className="w-4 h-4 text-teal-600" />
            <span>AI Summarize Experiment</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            <select
              value={activeExp.status}
              onChange={(e) => handleStatusChange(e.target.value as Experiment['status'])}
              className="bg-slate-50 border border-slate-200 text-xs font-bold rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500"
            >
              <option value="Draft">Draft</option>
              <option value="In Progress">In Progress</option>
              <option value="Under Review">Under Review</option>
              <option value="Completed">Completed</option>
            </select>
          </div>

          <button
            onClick={() => onSaveExperiment(activeExp)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Save Notebook</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Notebook Content (Left 2 cols) & AI Copilot Panel (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - ELN Notebook Document */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Metadata Bar */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400 font-medium block mb-1">Author</span>
              <span className="font-semibold text-slate-800 flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-blue-500" />
                {activeExp.author}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block mb-1">Date Created</span>
              <span className="font-semibold text-slate-800 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-blue-500" />
                {activeExp.date}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block mb-1">Attachments</span>
              <span className="font-semibold text-slate-800 flex items-center gap-1">
                <Paperclip className="w-3.5 h-3.5 text-blue-500" />
                {activeExp.attachmentsCount} Files
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

          {/* Section 1: Objective */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-2">
              <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-bold">1</span>
              <span>Objective & Hypothesis</span>
            </h3>
            <textarea
              rows={3}
              value={activeExp.objective}
              onChange={(e) => setActiveExp({ ...activeExp, objective: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 leading-relaxed focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          {/* Section 2: Materials & Sample Links */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 text-xs flex items-center justify-center font-bold">2</span>
                <span>Materials & Reagents (Sample Registry Linkage)</span>
              </div>
              <button 
                onClick={() => onSelectView('samples')}
                className="text-xs text-teal-600 hover:text-teal-700 font-semibold flex items-center gap-1"
              >
                <TestTube2 className="w-3.5 h-3.5" />
                <span>+ Link Sample from Registry</span>
              </button>
            </h3>

            <div className="divide-y divide-slate-100">
              {activeExp.materials.map((mat) => (
                <div key={mat.id} className="py-2.5 flex items-center justify-between text-xs">
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
            </div>
          </div>

          {/* Section 3: Protocol Steps */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs flex items-center justify-center font-bold">3</span>
                <span>Standard Protocol Execution Steps</span>
              </div>
              <span className="text-xs text-slate-400 font-normal">{activeExp.protocolSteps.length} SOP Steps</span>
            </h3>

            <div className="space-y-3">
              {activeExp.protocolSteps.map((step, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-3 text-xs">
                  <span className="font-bold text-blue-600 shrink-0 mt-0.5">{idx + 1}.</span>
                  <p className="flex-1 text-slate-700 leading-relaxed">{step}</p>
                </div>
              ))}
            </div>

            {/* Add Step Input */}
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
                className="bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                <span>Add Step</span>
              </button>
            </div>
          </div>

          {/* Section 4: Results */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-2">
              <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs flex items-center justify-center font-bold">4</span>
              <span>Observations & Experimental Results</span>
            </h3>
            <textarea
              rows={4}
              value={activeExp.results}
              onChange={(e) => setActiveExp({ ...activeExp, results: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 leading-relaxed focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          {/* Section 5: Collaboration Comments */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-2">
              <MessageSquare className="w-4 h-4 text-blue-600" />
              <span>Comments & Peer Review ({comments.length})</span>
            </h3>

            <div className="space-y-3">
              {comments.map((c) => (
                <div key={c.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
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
                placeholder="Write a comment or mention @Dr. Sarah..."
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddComment}
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
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
                RAG Active
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Generate SOP protocols, summarize complex experiments, and ground scientific Q&A in lab data.
            </p>

            <div className="space-y-2">
              <button
                onClick={handleGenerateAiProtocol}
                disabled={isAiDrafting}
                className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white text-xs font-bold rounded-lg shadow-md transition-all flex items-center justify-center gap-2"
              >
                <Bot className="w-4 h-4" />
                <span>{isAiDrafting ? 'Drafting SOP Protocol...' : 'AI Protocol Generator'}</span>
              </button>

              <button
                onClick={() => setShowSummarizeModal(true)}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <FileText className="w-3.5 h-3.5 text-teal-400" />
                <span>AI Experiment Summarizer</span>
              </button>

              <button
                onClick={() => onSelectView('sequences')}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Tag className="w-3.5 h-3.5 text-blue-400" />
                <span>Cross-Ref DNA Sequence</span>
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* AI Experiment Summarization Modal (Section 2.4 #1 Scope) */}
      {showSummarizeModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-2xl shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-teal-600" />
                <h3 className="text-base font-bold text-slate-800">AI Structured Experiment Summary</h3>
              </div>
              <button onClick={() => setShowSummarizeModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-blue-600 mb-1">1. Objective</p>
                <p className="text-slate-700">{activeExp.summary?.objective || activeExp.objective}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-teal-600 mb-1">2. Method / SOP</p>
                <p className="text-slate-700">{activeExp.summary?.method || 'Standard lipofectamine 3000 transfection and 48h culture.'}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-emerald-600 mb-1">3. Result</p>
                <p className="text-slate-700">{activeExp.summary?.result || activeExp.results}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-indigo-600 mb-1">4. Scientific Conclusion</p>
                <p className="text-slate-700">{activeExp.summary?.conclusion || 'Confirmed target cleavage. Proceed with functional validation.'}</p>
              </div>

              {activeExp.summary?.citations && (
                <div className="pt-2 border-t border-slate-100 flex items-center gap-2">
                  <span className="font-bold text-slate-500">Source Grounding Citations:</span>
                  {activeExp.summary.citations.map((c, i) => (
                    <span key={i} className="bg-blue-50 text-blue-600 font-mono text-[10px] px-2 py-0.5 rounded border border-blue-200">
                      {c.text}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowSummarizeModal(false)}
                className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-900 text-white rounded-lg"
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
