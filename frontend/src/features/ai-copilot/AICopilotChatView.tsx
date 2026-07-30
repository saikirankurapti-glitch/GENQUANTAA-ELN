import React, { useState } from 'react';
import type { AIChatMessage, ViewMode } from '../../types';
import { Bot, Sparkles, Send, ArrowUpRight, ShieldAlert, RefreshCw } from 'lucide-react';

interface AICopilotChatViewProps {
  chatMessages: AIChatMessage[];
  onSendMessage: (text: string) => void;
  onSelectView: (view: ViewMode) => void;
}

export const AICopilotChatView: React.FC<AICopilotChatViewProps> = ({
  chatMessages,
  onSendMessage,
  onSelectView
}) => {
  const [inputText, setInputText] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);

  const suggestedPrompts = [
    'Generate a 5-step SOP CRISPR transfection protocol for HEK293T cells',
    'Summarize all experimental findings in Project 101 (Objective, Method, Result, Conclusion)',
    'Recommend optimal primer annealing temperature for Gene X',
    'Search past lab entries for Western Blotting kinase protocol'
  ];

  const handleSend = (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim()) return;

    onSendMessage(text);
    setInputText('');
    setIsSimulating(true);

    setTimeout(() => {
      setIsSimulating(false);
    }, 1200);
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto h-[calc(100vh-5rem)] flex flex-col">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-5 rounded-2xl text-white shadow-lg flex items-center justify-between border border-slate-800 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500/20 text-teal-400 border border-teal-500/30 flex items-center justify-center">
            <Bot className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold">AI Research Copilot (RAG Grounded Scientific Q&A)</h2>
          </div>
        </div>
        <span className="text-xs bg-emerald-500/20 text-emerald-300 font-mono px-3 py-1 rounded-full border border-emerald-500/30">
          Response Latency &lt;15s
        </span>
      </div>

      {/* Suggested Prompts Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 shrink-0">
        {suggestedPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="text-xs bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-600 border border-slate-200 hover:border-blue-300 px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors shadow-sm font-medium cursor-pointer"
          >
            💡 {p}
          </button>
        ))}
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 overflow-y-auto space-y-6">
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'ai' && (
              <div className="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-2xl space-y-3 ${
              msg.sender === 'user'
                ? 'bg-blue-600 text-white rounded-2xl rounded-tr-none p-4 text-xs leading-relaxed shadow-sm'
                : 'bg-slate-50 text-slate-800 rounded-2xl rounded-tl-none p-5 border border-slate-200 text-xs leading-relaxed space-y-3'
            }`}>
              <p>{msg.text}</p>

              {/* Grounding Source Citations Pill */}
              {msg.citations && (
                <div className="pt-2 border-t border-slate-200/60 flex items-center gap-2 flex-wrap text-[11px]">
                  <span className="font-bold text-slate-500">Source Grounding Records:</span>
                  {msg.citations.map((c, i) => (
                    <button
                      key={i}
                      onClick={() => onSelectView(c.viewTarget)}
                      className="bg-blue-100 hover:bg-blue-200 text-blue-800 font-mono px-2 py-0.5 rounded border border-blue-300 flex items-center gap-1 transition-colors cursor-pointer"
                    >
                      <span>{c.label}</span>
                      <ArrowUpRight className="w-3 h-3 text-blue-600" />
                    </button>
                  ))}
                </div>
              )}

              {/* Protocol Card inside AI Response */}
              {msg.protocolData && (
                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3 text-slate-800">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div>
                      <span className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                        {msg.protocolData.title}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">Code: {msg.protocolData.sopCode}</span>
                    </div>
                    <span className="text-[10px] bg-teal-50 text-teal-700 font-bold px-2 py-0.5 rounded border border-teal-200">
                      AI Generated SOP
                    </span>
                  </div>

                  {msg.protocolData.safetyPrecautions && (
                    <div className="p-2.5 bg-amber-50 rounded-lg border border-amber-200 text-amber-900 text-[11px] flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
                      <span>{msg.protocolData.safetyPrecautions}</span>
                    </div>
                  )}

                  <div className="space-y-2">
                    {msg.protocolData.steps.map((step, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <span className="font-bold text-teal-600 mt-0.5">{idx + 1}.</span>
                        <span className="text-slate-700">{step}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-2 pt-2 border-t border-slate-100">
                    <button 
                      onClick={() => onSelectView('eln')}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <span>Insert into Active Notebook</span>
                    </button>
                    <button className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer">
                      Copy Text
                    </button>
                  </div>
                </div>
              )}

              <span className="text-[10px] text-slate-400 block text-right font-mono">{msg.timestamp}</span>
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs shrink-0 mt-1">
                NS
              </div>
            )}
          </div>
        ))}

        {isSimulating && (
          <div className="flex items-center gap-3 text-xs text-teal-600 font-medium">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>AI Copilot is searching RAG vector index & grounding response...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3 shrink-0">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask AI Copilot to write protocols, query lab data, or summarize findings..."
          className="flex-1 text-xs border-none focus:outline-none px-2 text-slate-800"
        />
        <button
          onClick={() => handleSend()}
          className="bg-teal-600 hover:bg-teal-700 text-white p-2.5 rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
