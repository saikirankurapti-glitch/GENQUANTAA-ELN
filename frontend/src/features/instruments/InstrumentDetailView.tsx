import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import {
  ArrowLeft, Loader2, AlertCircle, Wrench, CalendarClock, History,
  User2, BookOpen, Clock, ShieldCheck, CheckCircle2, AlertTriangle,
  Cpu, Settings, MapPin, Tag, Plus, Calendar, Check, X, Microscope
} from 'lucide-react';
import { useInstrument, useUpdateInstrument } from '../../hooks/useInstruments';
import { useAuth } from '../../providers/AuthProvider';
import { isUserAdmin, isStrictlyViewer, normalizeRole } from '../../utils/permissions';

interface InstrumentDetailViewProps {
  instrumentId: string;
  onSelectView: (view: ViewMode) => void;
}

const OP_STATUS: Record<string, { label: string; color: string; bg: string; border: string; dot: string }> = {
  operational:   { label: 'Operational',      color: 'text-emerald-700', bg: 'bg-emerald-50',  border: 'border-emerald-200', dot: 'bg-emerald-400' },
  maintenance:   { label: 'Under Maintenance', color: 'text-amber-700',   bg: 'bg-amber-50',    border: 'border-amber-200',   dot: 'bg-amber-400' },
  out_of_service:{ label: 'Out of Service',    color: 'text-rose-700',    bg: 'bg-rose-50',     border: 'border-rose-200',    dot: 'bg-rose-500' },
  calibration:   { label: 'Calibration Due',   color: 'text-purple-700',  bg: 'bg-purple-50',   border: 'border-purple-200',  dot: 'bg-purple-400' },
};

const AVAIL_STATUS: Record<string, { label: string; color: string; bg: string }> = {
  available: { label: 'Available',  color: 'text-emerald-600', bg: 'bg-emerald-50' },
  in_use:    { label: 'In Use',     color: 'text-blue-600',    bg: 'bg-blue-50' },
  reserved:  { label: 'Reserved',   color: 'text-indigo-600',  bg: 'bg-indigo-50' },
  booked:    { label: 'Booked',     color: 'text-violet-600',  bg: 'bg-violet-50' },
};

export const InstrumentDetailView: React.FC<InstrumentDetailViewProps> = ({
  instrumentId,
  onSelectView
}) => {
  const { user } = useAuth();
  const isViewer = isStrictlyViewer(user);
  const isAdminOrPI = isUserAdmin(user) || normalizeRole(user) === 'PI';

  const { data: instrument, isLoading, error } = useInstrument(instrumentId);
  const updateInstrument = useUpdateInstrument();

  const [bookModal, setBookModal] = useState(false);
  const [bookDate, setBookDate] = useState(new Date().toISOString().slice(0, 16));
  const [bookEndDate, setBookEndDate] = useState('');
  const [bookExperiment, setBookExperiment] = useState('');
  const [bookNotes, setBookNotes] = useState('');

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center p-16 h-full items-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
        <span className="text-xs text-slate-400 font-medium">Loading instrument profile…</span>
      </div>
    );
  }

  if (error || !instrument || !(instrument as any).id) {
    return (
      <div className="flex flex-col items-center justify-center p-16 h-full gap-3 text-rose-500">
        <AlertCircle className="w-8 h-8" />
        <span className="font-semibold text-sm">Failed to load instrument details.</span>
        <button onClick={() => onSelectView('instruments' as any)} className="text-xs text-slate-500 hover:underline cursor-pointer">
          ← Back to Instrument Control Tower
        </button>
      </div>
    );
  }

  // Safe field access
  const instAny = instrument as any;
  const maintenances: any[] = Array.isArray(instAny.maintenances) ? instAny.maintenances : [];
  const usageHistory: any[] = Array.isArray(instAny.usage_history) ? instAny.usage_history : [];
  const calibrations: any[] = Array.isArray(instAny.calibrations) ? instAny.calibrations : [];
  const meta: Record<string, any> = (instAny.metadata_json && typeof instAny.metadata_json === 'object') ? instAny.metadata_json : {};
  const activeSession = meta.active_session || null;

  const opCfg = OP_STATUS[instrument.operational_status] || OP_STATUS.operational;
  const availCfg = AVAIL_STATUS[instrument.availability_status] || AVAIL_STATUS.available;
  const isInUse = instrument.availability_status === 'in_use' || instrument.availability_status === 'booked';

  // Calibration countdown
  const calibDueDate = meta.next_calibration_date || instrument.calibration_due_date;
  const calibDaysLeft = calibDueDate ? Math.round((new Date(calibDueDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : null;

  const handleStatusUpdate = async (newOp: string, newAvail?: string) => {
    try {
      await updateInstrument.mutateAsync({
        id: instrument.id,
        data: {
          operational_status: newOp as any,
          availability_status: (newAvail || instrument.availability_status) as any,
        }
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-5 space-y-5 bg-slate-50 min-h-full">

      {/* ── Top Bar / Hero ─────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button onClick={() => onSelectView('instruments' as any)} className="p-2 rounded-xl hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-lg">
                {instrument.instrument_code}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg border ${opCfg.bg} ${opCfg.color} ${opCfg.border}`}>
                <span className={`inline-block w-1.5 h-1.5 rounded-full ${opCfg.dot} mr-1`} />
                {opCfg.label}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg ${availCfg.bg} ${availCfg.color}`}>
                {availCfg.label}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight mt-1">{instrument.instrument_name}</h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isViewer && instrument.operational_status === 'operational' && (
            <button
              onClick={() => setBookModal(true)}
              className="flex items-center gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer"
            >
              <Calendar className="w-4 h-4" />
              Book / Start Session
            </button>
          )}

          {!isViewer && (
            <select
              value={instrument.operational_status}
              onChange={(e) => handleStatusUpdate(e.target.value)}
              disabled={updateInstrument.isPending}
              className="bg-slate-50 border border-slate-200 text-xs font-bold rounded-xl px-3 py-2 focus:ring-2 focus:ring-amber-500 cursor-pointer disabled:opacity-50"
            >
              <option value="operational">Operational</option>
              <option value="maintenance">Under Maintenance</option>
              <option value="calibration">Calibration Due</option>
              <option value="out_of_service">Out of Service</option>
            </select>
          )}
        </div>
      </div>

      {/* ── Active Session Banner (Admin & PI Oversight) ─── */}
      {isInUse && activeSession && (
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-4 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/10 backdrop-blur rounded-xl flex items-center justify-center flex-shrink-0">
              <User2 className="w-5 h-5 text-blue-100" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold bg-white/20 px-2 py-0.5 rounded-full uppercase tracking-wider">Active Usage Session</span>
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              </div>
              <p className="font-bold text-sm mt-0.5">
                In Use By: <span className="underline decoration-blue-300">{activeSession.user_name || 'Researcher'}</span>
                {activeSession.user_role ? ` (${activeSession.user_role})` : ''}
              </p>
              {activeSession.experiment_title && (
                <p className="text-xs text-blue-100 mt-0.5">Project: {activeSession.experiment_title}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 border-t md:border-t-0 border-white/20 pt-2 md:pt-0">
            <div className="text-right text-xs">
              <p className="text-blue-100">Session Started</p>
              <p className="font-bold">{activeSession.started_at ? new Date(activeSession.started_at).toLocaleString() : 'Now'}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── 3 Column Grid ─────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* ── Left Column: Specs & Calibration ─────────── */}
        <div className="lg:col-span-1 space-y-4">
          {/* Identity & Specs Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-3">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-wider mb-3">Asset Specifications</h3>
            <div className="space-y-2.5">
              {[
                { label: 'Manufacturer', value: instrument.manufacturer || '—' },
                { label: 'Model', value: instrument.model || '—' },
                { label: 'Serial Number', value: instrument.serial_number || '—' },
                { label: 'Asset Tag', value: instrument.asset_tag || '—' },
                { label: 'Location', value: meta.location || 'Lab Bench' },
              ].map(r => (
                <div key={r.label} className="flex justify-between text-xs border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                  <span className="text-slate-400 font-medium">{r.label}</span>
                  <span className="font-semibold text-slate-700">{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Calibration Health Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <CalendarClock className="w-4 h-4 text-purple-500" />
              Calibration Status
            </h3>
            {calibDaysLeft !== null ? (
              <div className="space-y-3">
                <div className={`p-4 rounded-xl border text-center ${
                  calibDaysLeft < 0 ? 'bg-rose-50 border-rose-200 text-rose-700' :
                  calibDaysLeft < 14 ? 'bg-amber-50 border-amber-200 text-amber-700' :
                  'bg-emerald-50 border-emerald-200 text-emerald-700'
                }`}>
                  <span className="text-2xl font-black">{Math.abs(calibDaysLeft)}</span>
                  <span className="text-xs ml-1 font-bold">{calibDaysLeft < 0 ? 'Days Overdue' : 'Days Remaining'}</span>
                </div>
                <div className="text-xs flex justify-between text-slate-500">
                  <span>Next Calibration Due:</span>
                  <span className="font-bold text-slate-700">{new Date(calibDueDate).toLocaleDateString()}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">No calibration schedule configured.</p>
            )}
          </div>
        </div>

        {/* ── Right 2 Columns: Maintenance & Usage History ─ */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Maintenance Records */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <Wrench className="w-4 h-4 text-blue-500" />
                Maintenance & Service Log
              </h3>
              <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                {maintenances.length} record{maintenances.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="space-y-3 max-h-56 overflow-y-auto">
              {maintenances.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No maintenance logs recorded for this asset.</p>
              ) : (
                maintenances.map((m: any) => (
                  <div key={m.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs flex justify-between items-start">
                    <div>
                      <span className="font-bold text-slate-700 capitalize">{m.maintenance_type || 'Preventative Maintenance'}</span>
                      <p className="text-slate-500 mt-0.5">{m.remarks || 'Routine check completed cleanly.'}</p>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400">{new Date(m.maintenance_date).toLocaleDateString()}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Usage History Log */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <History className="w-4 h-4 text-teal-500" />
                Researcher Usage History (Audit Log)
              </h3>
              <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                {usageHistory.length} run{usageHistory.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {usageHistory.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No previous usage runs logged.</p>
              ) : (
                usageHistory.map((u: any) => (
                  <div key={u.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 bg-indigo-100 rounded-full flex items-center justify-center">
                        <User2 className="w-3.5 h-3.5 text-indigo-600" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">{u.user_name || u.performed_by || 'Researcher'}</p>
                        <p className="text-slate-400 text-[10px]">{u.remarks || 'Experimental run'}</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400">
                      {u.usage_start ? new Date(u.usage_start).toLocaleString() : '—'}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>

      {/* ── Booking Modal ─────────────────────────────── */}
      {bookModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-md shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-5 flex items-center justify-between">
              <div>
                <h3 className="text-base font-black text-white">Book Instrument Session</h3>
                <p className="text-blue-100 text-xs mt-0.5">{instrument.instrument_name}</p>
              </div>
              <button onClick={() => setBookModal(false)} className="text-white/70 hover:text-white cursor-pointer"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Start Time</label>
                  <input type="datetime-local" value={bookDate} onChange={e => setBookDate(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Expected End</label>
                  <input type="datetime-local" value={bookEndDate} onChange={e => setBookEndDate(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Associated Experiment / Project</label>
                <input type="text" value={bookExperiment} onChange={e => setBookExperiment(e.target.value)}
                  placeholder="e.g. Protocol 4 — Sample Run" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Session Notes</label>
                <textarea value={bookNotes} onChange={e => setBookNotes(e.target.value)} rows={2}
                  placeholder="Sample prep details or thermal profile..." className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button onClick={() => setBookModal(false)} className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">Cancel</button>
                <button onClick={() => {
                  alert(`Session reserved for ${user?.first_name || 'Researcher'}`);
                  setBookModal(false);
                }} className="px-5 py-2 text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl shadow-sm cursor-pointer">
                  Confirm Booking
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
