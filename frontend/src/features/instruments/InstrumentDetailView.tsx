import React from 'react';
import type { ViewMode } from '../../types';
import { ArrowLeft, Loader2, AlertCircle, Wrench, CalendarClock, History } from 'lucide-react';
import { useInstrument } from '../../hooks/useInstruments';

interface InstrumentDetailViewProps {
  instrumentId: string;
  onSelectView: (view: ViewMode) => void;
}

export const InstrumentDetailView: React.FC<InstrumentDetailViewProps> = ({
  instrumentId,
  onSelectView
}) => {
  const { data: instrument, isLoading, error } = useInstrument(instrumentId);

  if (isLoading) return <div className="flex justify-center p-12 h-full items-center"><Loader2 className="w-8 h-8 animate-spin text-amber-600" /></div>;
  if (error || !instrument) return <div className="flex justify-center p-12 h-full text-rose-500"><AlertCircle className="w-8 h-8" /></div>;

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => onSelectView('instruments' as any)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-mono">{instrument.instrument_code}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{instrument.instrument_name}</h2>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${instrument.operational_status === 'operational' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
            {instrument.operational_status.toUpperCase()}
          </span>
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${instrument.availability_status === 'available' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
            {instrument.availability_status.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-blue-500" /> Maintenance
          </h3>
          <div className="space-y-3 h-48 overflow-y-auto">
            {instrument.maintenances.length === 0 ? (
              <p className="text-xs text-slate-500">No maintenance recorded.</p>
            ) : (
              instrument.maintenances.map((m) => (
                <div key={m.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-slate-700 capitalize">{m.maintenance_type}</span>
                    <span className="text-slate-500">{new Date(m.maintenance_date).toLocaleDateString()}</span>
                  </div>
                  <p className="text-slate-600">{m.remarks}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <History className="w-4 h-4 text-teal-500" /> Usage History
          </h3>
          <div className="space-y-3 h-48 overflow-y-auto">
            {instrument.usage_history.length === 0 ? (
              <p className="text-xs text-slate-500">No usage recorded.</p>
            ) : (
              instrument.usage_history.map((tx) => (
                <div key={tx.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                  <p className="text-slate-500 mb-1">{new Date(tx.usage_start).toLocaleString()}</p>
                  <p className="font-bold text-slate-800">{tx.remarks || 'Standard run'}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
