import React, { useState } from 'react';
import { 
  ShieldCheck, MessageSquarePlus, CheckCircle, Clock, Reply, 
  Send, ChevronDown, ChevronUp, AlertTriangle, Check, RotateCcw, 
  Filter, Sparkles, User, Tag
} from 'lucide-react';
import type { QAComment } from '../../types';
import { useQAComments, useAddQAComment, useReplyQAComment, useResolveQAComment } from '../../hooks/useQAComments';

interface QAInlineReviewPanelProps {
  experimentId: string;
  selectedSectionId?: string | null;
  onSelectSection?: (sectionId: string) => void;
  activeTargetQuote?: string | null;
  onClearTargetQuote?: () => void;
}

export const QAInlineReviewPanel: React.FC<QAInlineReviewPanelProps> = ({
  experimentId,
  selectedSectionId,
  onSelectSection,
  activeTargetQuote,
  onClearTargetQuote
}) => {
  const { data: comments = [], isLoading } = useQAComments(experimentId);
  const addComment = useAddQAComment();
  const replyComment = useReplyQAComment();
  const resolveComment = useResolveQAComment();

  const [filter, setFilter] = useState<'all' | 'open' | 'resolved'>('all');
  const [expandedThreads, setExpandedThreads] = useState<Record<string, boolean>>({});
  const [replyTextMap, setReplyTextMap] = useState<Record<string, string>>({});
  
  // New comment composer state
  const [isCreatingComment, setIsCreatingComment] = useState(false);
  const [newSectionId, setNewSectionId] = useState('objective');
  const [newSectionTitle, setNewSectionTitle] = useState('Objective & Hypothesis');
  const [newTargetQuote, setNewTargetQuote] = useState('');
  const [newCommentText, setNewCommentText] = useState('');
  const [newCategory, setNewCategory] = useState<'QA_REVIEW' | 'COMPLIANCE_CHECK' | 'SCIENTIFIC_QUESTION' | 'SUGGESTION'>('QA_REVIEW');

  // If activeTargetQuote or selectedSectionId props change, prefill creation state
  React.useEffect(() => {
    if (selectedSectionId) {
      setNewSectionId(selectedSectionId);
      const titleMap: Record<string, string> = {
        objective: '1. Objective & Hypothesis',
        materials: '2. Materials & Reagents',
        steps: '3. Protocol Execution Steps',
        results: '4. Observations & Results',
      };
      setNewSectionTitle(titleMap[selectedSectionId] || selectedSectionId.replace('_', ' ').toUpperCase());
      setIsCreatingComment(true);
    }
    if (activeTargetQuote) {
      setNewTargetQuote(activeTargetQuote);
      setIsCreatingComment(true);
    }
  }, [selectedSectionId, activeTargetQuote]);

  const toggleThread = (id: string) => {
    setExpandedThreads(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCreateComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommentText.trim()) return;

    await addComment.mutateAsync({
      experimentId,
      data: {
        section_id: newSectionId,
        section_title: newSectionTitle,
        target_text: newTargetQuote.trim() || undefined,
        comment: newCommentText.trim(),
        category: newCategory,
      }
    });

    setNewCommentText('');
    setNewTargetQuote('');
    setIsCreatingComment(false);
    if (onClearTargetQuote) onClearTargetQuote();
  };

  const handleSendReply = async (commentId: string) => {
    const text = replyTextMap[commentId]?.trim();
    if (!text) return;

    await replyComment.mutateAsync({
      experimentId,
      commentId,
      comment: text
    });

    setReplyTextMap(prev => ({ ...prev, [commentId]: '' }));
    // Ensure expanded
    setExpandedThreads(prev => ({ ...prev, [commentId]: true }));
  };

  const handleToggleResolve = async (comment: QAComment) => {
    const nextStatus = comment.status === 'open' ? 'resolved' : 'open';
    await resolveComment.mutateAsync({
      experimentId,
      commentId: comment.id,
      status: nextStatus,
      resolutionNote: nextStatus === 'resolved' ? 'Reviewed and verified by QA auditor' : undefined
    });
  };

  const filteredComments = comments.filter((c: QAComment) => {
    if (filter === 'open') return c.status === 'open';
    if (filter === 'resolved') return c.status === 'resolved';
    return true;
  });

  const openCount = comments.filter((c: QAComment) => c.status === 'open').length;
  const resolvedCount = comments.filter((c: QAComment) => c.status === 'resolved').length;

  const categoryLabels: Record<string, { label: string; bg: string; text: string }> = {
    QA_REVIEW: { label: 'QA Review', bg: 'bg-amber-100', text: 'text-amber-800' },
    COMPLIANCE_CHECK: { label: '21 CFR Compliance', bg: 'bg-emerald-100', text: 'text-emerald-800' },
    SCIENTIFIC_QUESTION: { label: 'Discrepancy Note', bg: 'bg-rose-100', text: 'text-rose-800' },
    SUGGESTION: { label: 'Audit Suggestion', bg: 'bg-blue-100', text: 'text-blue-800' },
  };

  return (
    <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-2xl border border-amber-500/30 space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
              QA Audit Review Threads
              <span className="text-[10px] bg-amber-400/20 text-amber-300 font-mono px-1.5 py-0.2 rounded border border-amber-400/30">
                QA ONLY
              </span>
            </h4>
            <p className="text-[11px] text-slate-400">Google Docs-style inline review notes & line threads</p>
          </div>
        </div>

        <button
          onClick={() => setIsCreatingComment(!isCreatingComment)}
          className="text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold transition-all flex items-center gap-1.5 shadow cursor-pointer"
        >
          <MessageSquarePlus className="w-3.5 h-3.5" />
          <span>{isCreatingComment ? 'Cancel' : '+ New Review Note'}</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between bg-slate-950/60 p-1.5 rounded-xl border border-slate-800 text-xs">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFilter('all')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer ${
              filter === 'all' ? 'bg-slate-800 text-amber-300 font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({comments.length})
          </button>
          <button
            onClick={() => setFilter('open')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer flex items-center gap-1 ${
              filter === 'open' ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>Open ({openCount})</span>
          </button>
          <button
            onClick={() => setFilter('resolved')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer flex items-center gap-1 ${
              filter === 'resolved' ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <CheckCircle className="w-3 h-3 text-emerald-400" />
            <span>Resolved ({resolvedCount})</span>
          </button>
        </div>
      </div>

      {/* Inline Review Note Composer */}
      {isCreatingComment && (
        <form onSubmit={handleCreateComment} className="bg-slate-950/80 border border-amber-500/40 rounded-xl p-3.5 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1">
              <Tag className="w-3 h-3" /> New QA Review Finding
            </span>
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value as any)}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-[10px] rounded px-2 py-1 focus:ring-1 focus:ring-amber-400"
            >
              <option value="QA_REVIEW">QA Review</option>
              <option value="COMPLIANCE_CHECK">21 CFR Compliance</option>
              <option value="SCIENTIFIC_QUESTION">Discrepancy Note</option>
              <option value="SUGGESTION">Audit Suggestion</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <label className="text-slate-400 text-[10px] block mb-1">Target Section</label>
              <select
                value={newSectionId}
                onChange={(e) => {
                  setNewSectionId(e.target.value);
                  const titleMap: Record<string, string> = {
                    objective: '1. Objective & Hypothesis',
                    materials: '2. Materials & Reagents',
                    steps: '3. Protocol Execution Steps',
                    results: '4. Observations & Results',
                  };
                  setNewSectionTitle(titleMap[e.target.value] || e.target.value);
                }}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1.5 text-xs focus:ring-1 focus:ring-amber-400"
              >
                <option value="objective">1. Objective & Hypothesis</option>
                <option value="materials">2. Materials & Reagents</option>
                <option value="steps">3. Protocol Execution Steps</option>
                <option value="results">4. Observations & Results</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-[10px] block mb-1">Target Line / Quote (Optional)</label>
              <input
                type="text"
                value={newTargetQuote}
                onChange={(e) => setNewTargetQuote(e.target.value)}
                placeholder="e.g. Step 2 incubator temp..."
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1.5 text-xs focus:ring-1 focus:ring-amber-400"
              />
            </div>
          </div>

          <div>
            <textarea
              rows={3}
              value={newCommentText}
              onChange={(e) => setNewCommentText(e.target.value)}
              placeholder="Enter QA audit finding, discrepancy question, or compliance requirement..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-amber-400 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => {
                setIsCreatingComment(false);
                if (onClearTargetQuote) onClearTargetQuote();
              }}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={addComment.isPending || !newCommentText.trim()}
              className="px-4 py-1.5 text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg shadow transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
            >
              <Send className="w-3 h-3" />
              <span>{addComment.isPending ? 'Posting...' : 'Post QA Note'}</span>
            </button>
          </div>
        </form>
      )}

      {/* Threads List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
        {isLoading && (
          <p className="text-xs text-slate-400 italic py-4 text-center">Loading QA review threads...</p>
        )}

        {!isLoading && filteredComments.length === 0 && (
          <div className="p-6 text-center rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-2">
            <ShieldCheck className="w-7 h-7 text-slate-600 mx-auto" />
            <p className="text-xs font-semibold text-slate-300">No QA review threads in this filter</p>
            <p className="text-[11px] text-slate-500">
              Click <strong>+ New Review Note</strong> or the comment icon next to any document line to annotate findings.
            </p>
          </div>
        )}

        {filteredComments.map((comment: QAComment) => {
          const isExpanded = expandedThreads[comment.id] ?? true;
          const isResolved = comment.status === 'resolved';
          const catInfo = categoryLabels[comment.category] || categoryLabels.QA_REVIEW;

          return (
            <div
              key={comment.id}
              className={`rounded-xl border transition-all p-3.5 space-y-2.5 ${
                isResolved 
                  ? 'bg-slate-950/40 border-slate-800 opacity-80' 
                  : 'bg-slate-950/80 border-amber-500/30 shadow-md hover:border-amber-500/50'
              }`}
            >
              {/* Thread Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${catInfo.bg} ${catInfo.text}`}>
                      {catInfo.label}
                    </span>
                    <button
                      onClick={() => onSelectSection && onSelectSection(comment.section_id)}
                      className="text-[10px] font-mono bg-slate-800 text-amber-300 hover:bg-slate-700 px-2 py-0.5 rounded border border-slate-700 transition-colors"
                      title="Click to locate section"
                    >
                      📍 {comment.section_title || comment.section_id}
                    </button>
                    {isResolved ? (
                      <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded flex items-center gap-1">
                        <Check className="w-3 h-3" /> Resolved
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Open
                      </span>
                    )}
                  </div>

                  {comment.target_text && (
                    <div className="bg-amber-500/10 border-l-2 border-amber-400 px-2 py-1 rounded text-[11px] text-amber-200 italic">
                      "{comment.target_text}"
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleToggleResolve(comment)}
                  disabled={resolveComment.isPending}
                  className={`text-[11px] font-semibold px-2 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1 ${
                    isResolved 
                      ? 'border-slate-700 text-slate-400 hover:bg-slate-800 hover:text-slate-200' 
                      : 'border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/20'
                  }`}
                  title={isResolved ? 'Reopen thread' : 'Mark as resolved'}
                >
                  {isResolved ? <RotateCcw className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
                  <span>{isResolved ? 'Reopen' : 'Resolve'}</span>
                </button>
              </div>

              {/* Main Comment Text */}
              <div className="space-y-1 pt-1">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-200 flex items-center gap-1">
                    <User className="w-3 h-3 text-amber-400" />
                    {comment.author_name} ({comment.author_role})
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {new Date(comment.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="text-xs text-slate-100 leading-relaxed pl-1">
                  {comment.comment}
                </p>
              </div>

              {/* Resolution Note if resolved */}
              {isResolved && comment.resolved_by && (
                <div className="text-[11px] bg-emerald-950/40 border border-emerald-500/30 p-2 rounded-lg text-emerald-300">
                  ✓ <strong>Resolved by {comment.resolved_by}:</strong> {comment.resolution_note || 'Issue addressed.'}
                </div>
              )}

              {/* Replies Accordion */}
              {comment.replies && comment.replies.length > 0 && (
                <div className="space-y-2 pt-1 border-t border-slate-800/80">
                  <button
                    onClick={() => toggleThread(comment.id)}
                    className="text-[11px] text-slate-400 hover:text-slate-200 font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    <span>{comment.replies.length} {comment.replies.length === 1 ? 'Reply' : 'Replies'}</span>
                  </button>

                  {isExpanded && (
                    <div className="space-y-2 pl-3 border-l border-slate-800">
                      {comment.replies.map((reply: any, rIdx: number) => (
                        <div key={reply.id || rIdx} className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 text-xs space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-slate-400">
                            <span className="font-semibold text-slate-300">
                              {reply.author_name} ({reply.author_role})
                            </span>
                            <span className="text-[9px] text-slate-500">
                              {new Date(reply.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-200 leading-relaxed">
                            {reply.comment}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Reply Input Box */}
              {!isResolved && (
                <div className="flex items-center gap-2 pt-1.5 border-t border-slate-800/60">
                  <input
                    type="text"
                    value={replyTextMap[comment.id] || ''}
                    onChange={(e) => setReplyTextMap(prev => ({ ...prev, [comment.id]: e.target.value }))}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendReply(comment.id)}
                    placeholder="Reply to this QA thread..."
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:ring-1 focus:ring-amber-400 focus:outline-none"
                  />
                  <button
                    onClick={() => handleSendReply(comment.id)}
                    disabled={replyComment.isPending || !replyTextMap[comment.id]?.trim()}
                    className="p-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg font-bold transition-colors cursor-pointer disabled:opacity-40"
                    title="Send Reply"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
