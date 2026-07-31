import React, { useState } from 'react';
import type { AIChatMessage, ViewMode } from '../../types';
import { Bot, Sparkles, Send, ArrowUpRight, ShieldAlert, RefreshCw, FileText, PlusCircle } from 'lucide-react';
import { aiCopilotService } from '../../services/aiCopilot.service';

interface AICopilotChatViewProps {
  chatMessages?: AIChatMessage[];
  onSendMessage?: (text: string) => void;
  onSelectView: (view: ViewMode) => void;
}

const RenderMarkdown: React.FC<{ content: string }> = ({ content }) => {
  if (!content) return null;

  const lines = content.split('\n');

  return (
    <div className="space-y-1.5 text-xs leading-relaxed text-slate-800">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1" />;

        // Header check
        if (trimmed.startsWith('#')) {
          const title = trimmed.replace(/^#+\s*/, '');
          return (
            <h3 key={idx} className="text-sm font-bold text-slate-900 mt-2 mb-1 border-b border-slate-200 pb-1">
              {title}
            </h3>
          );
        }

        // Bullet or numbered point check
        const isBullet = trimmed.startsWith('* ') || trimmed.startsWith('- ') || /^\d+\.\s/.test(trimmed);
        
        // Parse **bold** syntax inside line
        const parts = line.split(/(\*\*.*?\*\*)/g);
        const lineContent = parts.map((part, pIdx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <strong key={pIdx} className="font-bold text-slate-900">
                {part.slice(2, -2)}
              </strong>
            );
          }
          return part;
        });

        if (isBullet) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="text-teal-600 font-bold shrink-0">•</span>
              <span className="flex-1">{lineContent}</span>
            </div>
          );
        }

        return <p key={idx}>{lineContent}</p>;
      })}
    </div>
  );
};

export const AICopilotChatView: React.FC<AICopilotChatViewProps> = ({
  chatMessages: propMessages,
  onSendMessage,
  onSelectView
}) => {
  const [messages, setMessages] = useState<AIChatMessage[]>(propMessages || [
    {
      id: 'msg-1',
      sender: 'ai',
      text: 'Hello! I am your AI Research Copilot powered by Groq Llama-3. Ask me to design protocols, analyze lab data, or search your ELN records.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const suggestedPrompts = [
    'Generate a 5-step SOP CRISPR transfection protocol for HEK293T cells',
    'Summarize all experimental findings in Project 101 (Objective, Method, Result, Conclusion)',
    'Recommend optimal primer annealing temperature for Gene X',
    'Search past lab entries for Western Blotting kinase protocol'
  ];

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || isGenerating) return;

    const userMsg: AIChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsGenerating(true);

    if (onSendMessage) {
      onSendMessage(text);
    }

    try {
      const resp = await aiCopilotService.sendChatMessage({ message: text });
      const aiMsg: AIChatMessage = {
        id: resp.message_id || `ai-${Date.now()}`,
        sender: 'ai',
        text: resp.content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: AIChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text: 'Sorry, I encountered an issue connecting to Groq AI Copilot. Please ensure backend server is running.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
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
            <h2 className="text-lg font-bold">AI Research Copilot (Groq Llama-3.3 Grounded Q&A)</h2>
          </div>
        </div>
        <span className="text-xs bg-emerald-500/20 text-emerald-300 font-mono px-3 py-1 rounded-full border border-emerald-500/30">
          Response Latency &lt;3s (Groq Accelerated)
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
        {messages.map((msg) => (
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
              <RenderMarkdown content={msg.text} />

              {/* Action Bar for AI Responses */}
              {msg.sender === 'ai' && (
                <div className="pt-3 border-t border-slate-200/80 flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => onSelectView('eln')}
                    className="bg-teal-600 hover:bg-teal-700 text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    <span>Create ELN Experiment from this SOP</span>
                  </button>
                  <button
                    onClick={() => onSelectView('eln')}
                    className="bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
                  >
                    <FileText className="w-3.5 h-3.5 text-blue-600" />
                    <span>Insert into Active Notebook</span>
                  </button>
                </div>
              )}

              <span className="text-[10px] text-slate-400 block text-right font-mono">{msg.timestamp}</span>
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs shrink-0 mt-1">
                US
              </div>
            )}
          </div>
        ))}

        {isGenerating && (
          <div className="flex items-center gap-3 text-xs text-teal-600 font-medium">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Groq Llama-3 Copilot is generating response...</span>
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
          disabled={isGenerating}
          className="bg-teal-600 hover:bg-teal-700 text-white p-2.5 rounded-lg shadow-sm transition-colors cursor-pointer disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
