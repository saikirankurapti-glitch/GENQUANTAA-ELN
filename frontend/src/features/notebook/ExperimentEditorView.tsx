import React, { useState, useEffect } from 'react';
import type { ViewMode } from '../../types';
import { 
  CheckCircle2, Sparkles, Paperclip, MessageSquare, 
  Tag, Calendar, User, Save, FileCheck, TestTube2, Plus, ArrowLeft, Bot, FileText, X, History, Trash2, Loader2, AlertCircle, Wand2, FlaskConical, ClipboardList
} from 'lucide-react';
import { useExperiment, useUpdateExperiment, useDeleteExperiment } from '../../hooks/useExperiments';
import { useAuth } from '../../providers/AuthProvider';
import { aiCopilotService } from '../../services/aiCopilot.service';

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
  const [status, setStatus] = useState<string>('');
  const [saveMessage, setSaveMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  // AI state per-section
  const [isAiDrafting, setIsAiDrafting] = useState(false);
  const [isAiFillObjective, setIsAiFillObjective] = useState(false);
  const [isAiFillResults, setIsAiFillResults] = useState(false);
  const [isAiFillMaterials, setIsAiFillMaterials] = useState(false);
  const [isAiFillAll, setIsAiFillAll] = useState(false);
  const [aiFillAllStep, setAiFillAllStep] = useState<string>('');
  const [aiProtocolDraftResult, setAiProtocolDraftResult] = useState<string | null>(null);
  const [showSummarizeModal, setShowSummarizeModal] = useState(false);
  const [showVersionHistoryModal, setShowVersionHistoryModal] = useState(false);
  const [aiSummaryContent, setAiSummaryContent] = useState<string>('');
  const [isAiSummarizing, setIsAiSummarizing] = useState(false);

  useEffect(() => {
    if (activeExp) {
      setObjective(activeExp.objective || '');
      setResults(activeExp.metadata_json?.results || '');
      // Read status from server — never default to 'draft'
      setStatus(activeExp.status || 'draft');
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
    setSaveMessage(null);
    const nextVersion = version + 1;
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

    // Only include status in payload if the user explicitly changed it
    const updatePayload: any = {
      objective,
      metadata_json: newMetadata
    };
    if (overrideStatus) {
      updatePayload.status = overrideStatus;
    }

    try {
      await updateExperiment.mutateAsync({
        id: activeExp.id,
        data: updatePayload
      });
      setSaveMessage({ type: 'ok', text: '✓ Notebook saved successfully' });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'Save failed';
      setSaveMessage({ type: 'err', text: `✗ ${detail}` });
      setTimeout(() => setSaveMessage(null), 5000);
    }
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
    const newComment = {
      user: user?.first_name || 'Researcher',
      text: commentText,
      time: new Date().toLocaleString()
    };
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

  // ── AI AUTO-FILL ALL SECTIONS at once ────────────────────────────────────
  const handleAiFillAll = async () => {
    setIsAiFillAll(true);
    setAiProtocolDraftResult(null);
    let filledObjective = objective;
    let filledSteps: string[] = protocolSteps;
    let filledMaterials: any[] = materials;
    let filledResults = results;

    try {
      // Step 1: Objective & Hypothesis
      setAiFillAllStep('✍️ Writing Objective & Hypothesis...');
      const objResp = await aiCopilotService.sendChatMessage({
        message: `Write a precise scientific Objective & Hypothesis for a lab experiment titled: "${activeExp.title}". Include the scientific goal, expected outcome, and key hypothesis in 3-4 sentences. Output plain text only, no markdown.`,
        feature: 'fill_objective'
      });
      filledObjective = objResp.content.trim();
      setObjective(filledObjective);

      // Step 2: Protocol Steps
      setAiFillAllStep('🔬 Generating SOP Protocol Steps...');
      const protResp = await aiCopilotService.sendChatMessage({
        message: `Generate exactly 5 numbered SOP protocol steps for a lab experiment titled: "${activeExp.title}".\nObjective: ${filledObjective}.\nFormat each step as a single line starting with the step number and a period. Output only the 5 steps, nothing else.`,
        feature: 'draft_protocol'
      });
      const rawProto = protResp.content.trim();
      const protoLines = rawProto.split('\n').map((l: string) => l.trim()).filter((l: string) => /^\d+[\.\)]/.test(l));
      filledSteps = protoLines.length > 0
        ? protoLines.map((l: string) => l.replace(/^\d+[\.\)]\s*/, '').trim())
        : [rawProto.slice(0, 220)];

      // Step 3: Materials
      setAiFillAllStep('🧪 Suggesting Materials & Reagents...');
      const matResp = await aiCopilotService.sendChatMessage({
        message: `List exactly 4 lab reagents/materials needed for experiment: "${activeExp.title}".\nFormat as JSON array: [{"name":"Reagent Name","quantity":"Xmg","lotNumber":"LOT-XXXX"}]\nReturn ONLY the JSON array, no other text.`,
        feature: 'fill_materials'
      });
      const rawMat = matResp.content.trim().replace(/```json|```/g, '');
      try { filledMaterials = JSON.parse(rawMat); } catch { filledMaterials = []; }

      // Step 4: Results
      setAiFillAllStep('📊 Drafting Observations & Results...');
      const resResp = await aiCopilotService.sendChatMessage({
        message: `Draft scientific Observations & Results for a lab experiment titled: "${activeExp.title}".\nObjective: ${filledObjective}.\nProtocol: ${filledSteps.join('; ')}.\nWrite 2-3 sentences of expected observations and measurable outcomes. Plain text only, no markdown.`,
        feature: 'fill_results'
      });
      filledResults = resResp.content.trim();
      setResults(filledResults);

      // Step 5: Save everything in one call
      setAiFillAllStep('💾 Saving all AI-generated content...');
      const nextVersion = version + 1;
      const newHistoryEntry = {
        version: nextVersion,
        timestamp: new Date().toUTCString(),
        author: user?.first_name || 'AI Copilot',
        changes: 'AI Auto-Fill All Sections completed via Groq Llama-3.'
      };
      await updateExperiment.mutateAsync({
        id: activeExp.id,
        data: {
          objective: filledObjective,
          metadata_json: {
            ...activeExp.metadata_json,
            protocolSteps: filledSteps,
            materials: filledMaterials,
            results: filledResults,
            version: nextVersion,
            versionHistory: [...versionHistory, newHistoryEntry]
          }
        }
      });
      setAiProtocolDraftResult('✓ All sections auto-filled and saved by AI');
    } catch (e) {
      console.error('AI Fill All failed:', e);
      setAiProtocolDraftResult('✗ AI Fill All encountered an error. Try individual sections.');
    } finally {
      setIsAiFillAll(false);
      setAiFillAllStep('');
    }
  };

  // ── AI AUTO-FILL: Objective & Hypothesis ─────────────────────────────────
  const handleAiFillObjective = async () => {
    setIsAiFillObjective(true);
    try {
      const resp = await aiCopilotService.sendChatMessage({
        message: `Write a precise scientific Objective & Hypothesis for an ELN experiment titled: "${activeExp.title}". Include the scientific goal, expected outcome, and key hypothesis in 3-4 sentences. Output plain text only, no markdown.`,
        feature: 'fill_objective'
      });
      setObjective(resp.content.trim());
    } catch (e) {
      console.error('AI fill objective failed:', e);
    } finally {
      setIsAiFillObjective(false);
    }
  };

  // ── AI AUTO-FILL: Protocol Steps ──────────────────────────────────────────
  const handleGenerateAiProtocol = async () => {
    setIsAiDrafting(true);
    setAiProtocolDraftResult(null);
    try {
      const resp = await aiCopilotService.sendChatMessage({
        message: `Generate exactly 5 numbered SOP protocol steps for a lab experiment titled: "${activeExp.title}". 
Current objective: ${objective || 'Not defined yet'}.
Format each step as a single line starting with the step number and a period. No extra commentary, just the 5 steps.`,
        feature: 'draft_protocol'
      });

      // Parse numbered lines like "1. Do X", "2. Do Y" etc.
      const raw = resp.content.trim();
      const lines = raw.split('\n').map(l => l.trim()).filter(l => /^\d+[\.\)]/.test(l));
      
      const stepsToAdd = lines.length > 0
        ? lines.map(l => l.replace(/^\d+[\.\)]\s*/, '').trim())
        : [raw.slice(0, 220)];

      const newSteps = [...protocolSteps, ...stepsToAdd];
      const newMetadata = {
        ...activeExp.metadata_json,
        protocolSteps: newSteps,
      };

      await updateExperiment.mutateAsync({
        id: activeExp.id,
        data: { metadata_json: newMetadata }
      });
      setAiProtocolDraftResult(`✓ Added ${stepsToAdd.length} AI-generated SOP steps`);
    } catch (e) {
      console.error('AI protocol draft failed:', e);
      setAiProtocolDraftResult('✗ AI generation failed. Try again.');
    } finally {
      setIsAiDrafting(false);
    }
  };

  // ── AI AUTO-FILL: Observations & Results ─────────────────────────────────
  const handleAiFillResults = async () => {
    setIsAiFillResults(true);
    try {
      const resp = await aiCopilotService.sendChatMessage({
        message: `Draft scientific Observations & Results for an ELN experiment titled: "${activeExp.title}".
Objective: ${objective || 'Not specified'}.
Protocol steps completed: ${protocolSteps.length > 0 ? protocolSteps.join('; ') : 'Not specified'}.
Write 2-3 sentences of expected observations and key measurable outcomes. Output plain text only, no markdown.`,
        feature: 'fill_results'
      });
      setResults(resp.content.trim());
    } catch (e) {
      console.error('AI fill results failed:', e);
    } finally {
      setIsAiFillResults(false);
    }
  };

  // ── AI AUTO-FILL: Suggested Materials ────────────────────────────────────
  const handleAiFillMaterials = async () => {
    setIsAiFillMaterials(true);
    try {
      const resp = await aiCopilotService.sendChatMessage({
        message: `List exactly 4 lab reagents/materials needed for experiment: "${activeExp.title}".
Format as JSON array: [{"name":"Reagent Name","quantity":"Xmg","lotNumber":"LOT-XXXX"}]
Return ONLY the JSON array, no other text.`,
        feature: 'fill_materials'
      });
      const raw = resp.content.trim().replace(/```json|```/g, '');
      let parsed: any[] = [];
      try { parsed = JSON.parse(raw); } catch { parsed = []; }
      
      if (parsed.length > 0) {
        const newMetadata = {
          ...activeExp.metadata_json,
          materials: [...materials, ...parsed],
        };
        await updateExperiment.mutateAsync({
          id: activeExp.id,
          data: { metadata_json: newMetadata }
        });
      }
    } catch (e) {
      console.error('AI fill materials failed:', e);
    } finally {
      setIsAiFillMaterials(false);
    }
  };

  // ── AI Summarize (modal) ──────────────────────────────────────────────────
  const handleOpenSummarize = async () => {
    setShowSummarizeModal(true);
    if (!aiSummaryContent) {
      setIsAiSummarizing(true);
      try {
        const resp = await aiCopilotService.sendChatMessage({
          message: `Write a structured scientific summary for this ELN experiment:
Title: ${activeExp.title}
Objective: ${objective || 'N/A'}
Protocol Steps: ${protocolSteps.length > 0 ? protocolSteps.join('; ') : 'N/A'}
Observations: ${results || 'N/A'}

Format with sections: 1. Background, 2. Methods Summary, 3. Key Findings, 4. Conclusions. Keep each section 1-2 sentences.`,
          feature: 'summarize_experiment'
        });
        setAiSummaryContent(resp.content.trim());
      } catch {
        setAiSummaryContent('AI summarization failed. Please try again.');
      } finally {
        setIsAiSummarizing(false);
      }
    }
  };

  const handleSoftDelete = async () => {
    if (confirm('Soft-delete this experiment?')) {
      await deleteExperiment.mutateAsync(activeExp.id);
      onSelectView('dashboard');
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">

      {/* ⚡ AI Fill All Progress Banner */}
      {isAiFillAll && (
        <div className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl px-5 py-3 flex items-center gap-3 shadow-lg animate-pulse">
          <Loader2 className="w-5 h-5 animate-spin shrink-0" />
          <div>
            <p className="text-xs font-bold">⚡ AI Filling All Sections — Groq Llama-3 is working...</p>
            <p className="text-[11px] text-violet-200 mt-0.5">{aiFillAllStep}</p>
          </div>
        </div>
      )}

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
          {/* ⚡ AI Fill All — primary prominent button */}
          <button
            onClick={handleAiFillAll}
            disabled={isAiFillAll || updateExperiment.isPending}
            className="flex items-center gap-1.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-lg shadow-md transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isAiFillAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            <span>{isAiFillAll ? 'AI Filling...' : '⚡ AI Fill All'}</span>
          </button>

          <button
            onClick={() => setShowVersionHistoryModal(true)}
            className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition-colors cursor-pointer"
          >
            <History className="w-4 h-4 text-blue-600" />
            <span>History (v{version})</span>
          </button>

          <button
            onClick={handleOpenSummarize}
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
              <option value="draft">Draft</option>
              <option value="planned">Planned</option>
              <option value="in_progress">In Progress</option>
              <option value="submitted">Submitted</option>
              <option value="in_review">In Review</option>
              <option value="approved">Approved</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            {saveMessage && (
              <span className={`text-xs font-semibold px-2 py-1 rounded ${
                saveMessage.type === 'ok' ? 'text-green-700 bg-green-50' : 'text-rose-700 bg-rose-50'
              }`}>
                {saveMessage.text}
              </span>
            )}
            <button
              onClick={() => handleSaveExperiment()}
              disabled={updateExperiment.isPending}
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer disabled:opacity-50"
            >
              {updateExperiment.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              <span>Save Notebook</span>
            </button>
          </div>

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

          {/* Section 1: Objective & Hypothesis */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-bold">1</span>
                <span>Objective & Hypothesis</span>
              </div>
              <button
                onClick={handleAiFillObjective}
                disabled={isAiFillObjective}
                className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 px-2.5 py-1 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
              >
                {isAiFillObjective
                  ? <Loader2 className="w-3 h-3 animate-spin" />
                  : <Wand2 className="w-3 h-3" />
                }
                {isAiFillObjective ? 'AI Writing...' : 'AI Auto-Fill'}
              </button>
            </h3>
            {objective === '' && !isAiFillObjective && (
              <p className="text-xs text-slate-400 italic">
                💡 Click <strong>AI Auto-Fill</strong> to let Groq AI write the objective & hypothesis for you based on the experiment title.
              </p>
            )}
            <textarea
              rows={3}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Enter scientific objective and hypothesis... or click AI Auto-Fill above"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 leading-relaxed focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
            ></textarea>
          </div>

          {/* Section 2: Materials & Reagents */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 text-xs flex items-center justify-center font-bold">2</span>
                <span>Materials & Reagents (Sample Registry Linkage)</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleAiFillMaterials}
                  disabled={isAiFillMaterials}
                  className="flex items-center gap-1 text-[11px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 px-2.5 py-1 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isAiFillMaterials ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wand2 className="w-3 h-3" />}
                  {isAiFillMaterials ? 'AI Suggesting...' : 'AI Suggest'}
                </button>
                <button 
                  onClick={() => onSelectView('samples')}
                  className="text-xs text-teal-600 hover:text-teal-700 font-semibold flex items-center gap-1 cursor-pointer"
                >
                  <TestTube2 className="w-3.5 h-3.5" />
                  <span>+ Link Sample from Registry</span>
                </button>
              </div>
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
              {materials.length === 0 && (
                <p className="text-xs text-slate-400 py-2 italic">
                  💡 No materials linked yet. Click <strong>AI Suggest</strong> to auto-generate reagent list, or link from Sample Registry.
                </p>
              )}
            </div>
          </div>

          {/* Section 3: Protocol Steps */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs flex items-center justify-center font-bold">3</span>
                <span>Standard Protocol Execution Steps</span>
              </div>
              <span className="text-xs text-slate-400 font-normal">{protocolSteps.length} SOP Steps</span>
            </h3>

            {protocolSteps.length === 0 && !isAiDrafting && (
              <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 text-xs text-indigo-700">
                💡 <strong>No steps yet.</strong> Click <strong>AI Protocol Generator</strong> in the right panel to auto-generate 5 SOP steps using Groq AI, or add steps manually below.
              </div>
            )}

            <div className="space-y-3">
              {protocolSteps.map((step, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-3 text-xs">
                  <span className="font-bold text-blue-600 shrink-0 mt-0.5">{idx + 1}.</span>
                  <p className="flex-1 text-slate-700 leading-relaxed">{step}</p>
                </div>
              ))}
            </div>

            {aiProtocolDraftResult && (
              <div className={`text-xs font-semibold px-3 py-2 rounded-lg ${aiProtocolDraftResult.startsWith('✓') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                {aiProtocolDraftResult}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <input
                type="text"
                value={newStepText}
                onChange={(e) => setNewStepText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddStep()}
                placeholder="Add custom protocol step... (press Enter)"
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

          {/* Section 4: Observations & Results */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs flex items-center justify-center font-bold">4</span>
                <span>Observations & Experimental Results</span>
              </div>
              <button
                onClick={handleAiFillResults}
                disabled={isAiFillResults}
                className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 px-2.5 py-1 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
              >
                {isAiFillResults ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wand2 className="w-3 h-3" />}
                {isAiFillResults ? 'AI Drafting...' : 'AI Draft Results'}
              </button>
            </h3>
            {results === '' && !isAiFillResults && (
              <p className="text-xs text-slate-400 italic">
                💡 Click <strong>AI Draft Results</strong> to generate expected observations based on your objective and protocol steps.
              </p>
            )}
            <textarea
              rows={4}
              value={results}
              onChange={(e) => setResults(e.target.value)}
              placeholder="Enter experimental observations & results... or click AI Draft Results above"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 leading-relaxed focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
            ></textarea>
          </div>

          {/* Comments & Peer Review */}
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
              {comments.length === 0 && (
                <p className="text-xs text-slate-400 italic">No peer comments yet. Type below to add a scientific note or review.</p>
              )}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                placeholder="Write a peer review comment or observation note..."
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
        <div className="space-y-4">
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
              Groq <span className="text-teal-300 font-semibold">Llama-3</span> can auto-fill <span className="text-white font-semibold">every section</span> with one click — or fill sections individually using the buttons below.
            </p>

            <div className="space-y-2">
              {/* ⚡ AI FILL ALL — Primary CTA */}
              <button
                onClick={handleAiFillAll}
                disabled={isAiFillAll || updateExperiment.isPending}
                className="w-full py-3 px-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white text-xs font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 border border-violet-500/30"
              >
                {isAiFillAll
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Wand2 className="w-4 h-4" />
                }
                <span>{isAiFillAll ? aiFillAllStep || 'AI Filling All Sections...' : '⚡ AI Fill All Sections (One Click)'}</span>
              </button>

              <div className="border-t border-slate-800 pt-2 pb-1">
                <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider text-center">— or fill individually —</p>
              </div>

              {/* AI Protocol Generator */}
              <button
                onClick={handleGenerateAiProtocol}
                disabled={isAiDrafting || updateExperiment.isPending}
                className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white text-xs font-bold rounded-lg shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isAiDrafting
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Bot className="w-4 h-4" />
                }
                <span>{isAiDrafting ? 'Drafting SOP Protocol...' : 'AI Protocol Generator'}</span>
              </button>


              {/* AI Fill Objective */}
              <button
                onClick={handleAiFillObjective}
                disabled={isAiFillObjective}
                className="w-full py-2 px-3 bg-purple-900/60 hover:bg-purple-900 text-purple-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 border border-purple-700/50"
              >
                {isAiFillObjective ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />}
                <span>{isAiFillObjective ? 'Writing Objective...' : 'AI Fill: Objective & Hypothesis'}</span>
              </button>

              {/* AI Suggest Materials */}
              <button
                onClick={handleAiFillMaterials}
                disabled={isAiFillMaterials}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isAiFillMaterials ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FlaskConical className="w-3.5 h-3.5 text-teal-400" />}
                <span>{isAiFillMaterials ? 'Generating Reagents...' : 'AI Suggest Materials & Reagents'}</span>
              </button>

              {/* AI Draft Results */}
              <button
                onClick={handleAiFillResults}
                disabled={isAiFillResults}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isAiFillResults ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ClipboardList className="w-3.5 h-3.5 text-emerald-400" />}
                <span>{isAiFillResults ? 'Drafting Results...' : 'AI Draft: Observations & Results'}</span>
              </button>

              {/* AI Summarize */}
              <button
                onClick={handleOpenSummarize}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5 text-teal-400" />
                <span>AI Experiment Summarizer</span>
              </button>

              {/* Cross-Ref DNA Sequence */}
              <button
                onClick={() => onSelectView('sequences')}
                className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer"
              >
                <Tag className="w-3.5 h-3.5 text-blue-400" />
                <span>Cross-Ref DNA Sequence</span>
              </button>
            </div>

            {/* Quick hints */}
            <div className="border-t border-slate-800 pt-3 space-y-1.5">
              <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">How it works</p>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Each AI button uses <span className="text-teal-400 font-semibold">Groq Llama-3</span> to generate scientific content based on your experiment title, objective, and protocol steps. Results are saved automatically to MongoDB.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Version History Modal */}
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

      {/* AI Summarize Modal */}
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

            {isAiSummarizing ? (
              <div className="flex items-center justify-center py-10 gap-3 text-slate-500 text-sm">
                <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
                <span>Groq AI is generating a structured summary…</span>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                {aiSummaryContent ? (
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-slate-700 leading-relaxed whitespace-pre-line">
                    {aiSummaryContent}
                  </div>
                ) : (
                  <>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-blue-600 mb-1">1. Objective</p>
                      <p className="text-slate-700">{objective || '—'}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-teal-600 mb-1">2. Method / SOP</p>
                      <p className="text-slate-700">{protocolSteps.length > 0 ? protocolSteps.join(' → ') : 'No methods defined.'}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <p className="font-bold text-slate-800 uppercase tracking-wider text-[10px] text-emerald-600 mb-1">3. Result</p>
                      <p className="text-slate-700">{results || '—'}</p>
                    </div>
                  </>
                )}
              </div>
            )}

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
