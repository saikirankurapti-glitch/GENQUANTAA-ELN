import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { ArrowLeft, Loader2, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { useProtocol, useUpdateProtocol, useApproveProtocol } from '../../hooks/useProtocols';

interface ProtocolDetailViewProps {
  protocolId: string;
  onSelectView: (view: ViewMode) => void;
}

export const ProtocolDetailView: React.FC<ProtocolDetailViewProps> = ({
  protocolId,
  onSelectView
}) => {
  const { data: protocol, isLoading, error } = useProtocol(protocolId);
  const updateProtocol = useUpdateProtocol();
  const approveProtocol = useApproveProtocol();

  const handleApprove = async (status: string) => {
    if (!protocol) return;
    await approveProtocol.mutateAsync({
      id: protocol.id,
      data: { status, comments: "Reviewed via UI" }
    });
  };

  if (isLoading) return <div className="flex justify-center p-12 h-full items-center"><Loader2 className="w-8 h-8 animate-spin text-indigo-600" /></div>;
  if (error || !protocol) return <div className="flex justify-center p-12 h-full text-rose-500"><AlertCircle className="w-8 h-8" /></div>;

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => onSelectView('protocols')} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-mono">{protocol.protocol_code}</span>
              <span className="bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded">v{protocol.current_version}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{protocol.title}</h2>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${protocol.status === 'approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
            {protocol.status.toUpperCase()}
          </span>
          {protocol.status !== 'approved' && (
            <button onClick={() => handleApprove('approved')} className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer">
              <CheckCircle2 className="w-4 h-4" /> Approve
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2">Protocol Steps</h3>
        {protocol.steps.length === 0 ? (
          <p className="text-xs text-slate-500">No steps defined. (Use the API or full editor to add steps).</p>
        ) : (
          <div className="space-y-4">
            {protocol.steps.map((step) => (
              <div key={step.id} className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-sm">
                <div className="font-bold text-slate-800 mb-2">Step {step.step_number}: {step.title}</div>
                <p className="text-slate-600 whitespace-pre-wrap">{step.instructions}</p>
                {step.safety_notes && (
                  <div className="mt-3 p-2 bg-amber-50 text-amber-800 rounded border border-amber-200 text-xs flex gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{step.safety_notes}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
