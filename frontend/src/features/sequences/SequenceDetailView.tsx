import React from 'react';
import type { ViewMode } from '../../types';
import { ArrowLeft, Loader2, AlertCircle, Dna, FileText, QrCode } from 'lucide-react';
import { useSequence } from '../../hooks/useSequences';
import QRCode from 'react-qr-code';

interface SequenceDetailViewProps {
  sequenceId: string;
  onSelectView: (view: ViewMode) => void;
}

export const SequenceDetailView: React.FC<SequenceDetailViewProps> = ({
  sequenceId,
  onSelectView
}) => {
  const { data: sequence, isLoading, error } = useSequence(sequenceId);

  if (isLoading) return <div className="flex justify-center p-12 h-full items-center"><Loader2 className="w-8 h-8 animate-spin text-purple-600" /></div>;
  if (error || !sequence) return <div className="flex justify-center p-12 h-full text-rose-500"><AlertCircle className="w-8 h-8" /></div>;

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => onSelectView('sequence-registry' as any)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-mono">{sequence.sequence_code}</span>
              <span className="bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded">v{sequence.version}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{sequence.sequence_name}</h2>
          </div>
        </div>
        <div className="flex items-center gap-4 border-l border-slate-200 pl-4">
          <div className="flex flex-col items-end">
            <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Length</span>
            <span className="text-lg font-bold text-slate-800">{sequence.length} bp</span>
          </div>
          {sequence.gc_content !== undefined && sequence.gc_content !== null && (
            <div className="flex flex-col items-end">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">GC%</span>
              <span className="text-lg font-bold text-slate-800">{sequence.gc_content}%</span>
            </div>
          )}
          {sequence.molecular_weight !== undefined && sequence.molecular_weight !== null && (
            <div className="flex flex-col items-end">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Mol. Weight</span>
              <span className="text-lg font-bold text-slate-800">{sequence.molecular_weight} Da</span>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
          <Dna className="w-4 h-4 text-purple-500" /> Sequence Data
        </h3>
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 font-mono text-sm text-slate-700 break-all leading-loose">
          {sequence.sequence_data}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row gap-6 items-start">
        <div className="bg-white p-2 rounded-xl border border-slate-200 shadow-sm w-fit inline-block shrink-0">
          <QRCode 
            value={sequence.sequence_code} 
            size={120} 
            level="M"
            bgColor="#ffffff"
            fgColor="#1e293b" // slate-800
          />
        </div>
        <div className="space-y-2">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            <QrCode className="w-4 h-4 text-indigo-500" /> Print Label / Scan Tag
          </h3>
          <p className="text-sm text-slate-500 max-w-md leading-relaxed">
            Scan this QR code from any tablet or mobile device using the built-in scanner to instantly pull up this sequence record while working at the bench. 
          </p>
          <div className="mt-2 text-xs font-mono bg-slate-100 text-slate-600 px-3 py-1.5 rounded w-fit border border-slate-200">
            {sequence.sequence_code}
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-500" /> Annotations
        </h3>
        {sequence.annotations.length === 0 ? (
          <p className="text-xs text-slate-500">No annotations found.</p>
        ) : (
          <div className="space-y-3">
            {sequence.annotations.map(a => (
              <div key={a.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs flex justify-between">
                <div>
                  <span className="font-bold text-slate-800">{a.label}</span>
                  <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-bold">{a.annotation_type}</span>
                </div>
                <div className="font-mono text-slate-500">
                  [{a.start_position} - {a.end_position}]
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
