import React, { useState, useMemo } from 'react';
import type { ViewMode } from '../../types';
import {
  Search, Plus, ArrowUpRight, Loader2, AlertCircle,
  Wrench, CheckCircle2, XCircle, CalendarClock,
  X, Check, ChevronRight, Filter, Activity,
  User2, Users, Clock, Calendar, Tag, ShieldAlert,
  Cpu, Microscope, Zap, Settings, BookOpen, BarChart3,
  AlertTriangle, Eye
} from 'lucide-react';
import { useInstruments, useCreateInstrument } from '../../hooks/useInstruments';
import { useAuth } from '../../providers/AuthProvider';
import { isStrictlyViewer, isUserAdmin, normalizeRole } from '../../utils/permissions';

interface InstrumentRegistryViewProps {
  onSelectInstrument: (id: string) => void;
  onSelectView: (view: ViewMode) => void;
}

const INSTRUMENT_TYPES = [
  { code: '', label: 'All Types', icon: '🔬' },
  { code: 'CENTRIFUGE', label: 'Centrifuge', icon: '🔄' },
  { code: 'PCR', label: 'PCR Cycler', icon: '🧬' },
  { code: 'MICROSCOPE', label: 'Microscope', icon: '🔬' },
  { code: 'SPECTRO', label: 'Spectrophotometer', icon: '📡' },
  { code: 'INCUBATOR', label: 'Incubator', icon: '🌡️' },
  { code: 'GEL_ELECTRO', label: 'Gel Electrophoresis', icon: '⚡' },
  { code: 'FLOW_CYTO', label: 'Flow Cytometer', icon: '💧' },
  { code: 'SEQUENCER', label: 'Sequencer', icon: '🧪' },
];

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

// Parse "in_use_by" from metadata_json — this stores active usage session
const getActiveSession = (ins: any) => {
  return ins.metadata_json?.active_session || null;
};

export const InstrumentRegistryView: React.FC<InstrumentRegistryViewProps> = ({
  onSelectInstrument,
}) => {
  const { user } = useAuth();
  const isViewer = isStrictlyViewer(user);
  const isAdminOrPI = isUserAdmin(user) || normalizeRole(user) === 'PI';

  const [searchQuery, setSearchQuery] = useState('');
  const [opFilter, setOpFilter] = useState('');
  const [availFilter, setAvailFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Book / Use modal
  const [bookModal, setBookModal] = useState<{ id: string; name: string; code: string } | null>(null);
  const [bookDate, setBookDate] = useState(new Date().toISOString().slice(0, 16));
  const [bookEndDate, setBookEndDate] = useState('');
  const [bookExperiment, setBookExperiment] = useState('');
  const [bookNotes, setBookNotes] = useState('');
  const [bookMode, setBookMode] = useState<'use_now' | 'reserve'>('use_now');

  // New Instrument modal
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState(1);
  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState(`INS-${Math.floor(1000 + Math.random() * 9000)}`);
  const [newSerial, setNewSerial] = useState('');
  const [newAssetTag, setNewAssetTag] = useState('');
  const [newManufacturer, setNewManufacturer] = useState('');
  const [newModel, setNewModel] = useState('');
  const [newType, setNewType] = useState('MICROSCOPE');
  const [newLocation, setNewLocation] = useState('');
  const [newCalibDue, setNewCalibDue] = useState('');
  const [newNotes, setNewNotes] = useState('');

  const { data: instrumentData, isLoading, error } = useInstruments(
    page, pageSize, undefined,
    opFilter || undefined,
    availFilter || undefined,
    undefined,
    searchQuery
  );

  const createInstrument = useCreateInstrument();

  // KPIs
  const total = instrumentData?.total ?? 0;
  const operational = instrumentData?.items.filter(i => i.operational_status === 'operational').length ?? 0;
  const inMaintenance = instrumentData?.items.filter(i => i.operational_status === 'maintenance').length ?? 0;
  const outOfService = instrumentData?.items.filter(i => i.operational_status === 'out_of_service').length ?? 0;
  const inUseCount = instrumentData?.items.filter(i => i.availability_status === 'in_use' || i.availability_status === 'booked').length ?? 0;

  // Currently in use — for admin/PI panel
  const activeUsageSessions = useMemo(() => {
    if (!instrumentData?.items) return [];
    return instrumentData.items
      .filter(i => {
        const session = getActiveSession(i);
        return session && (i.availability_status === 'in_use' || i.availability_status === 'booked');
      })
      .map(i => ({ instrument: i, session: getActiveSession(i) }));
  }, [instrumentData]);

  // Type filter (local)
  const displayItems = useMemo(() => {
    if (!instrumentData?.items) return [];
    if (!typeFilter) return instrumentData.items;
    return instrumentData.items.filter(i => i.metadata_json?.instrument_type === typeFilter);
  }, [instrumentData, typeFilter]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await createInstrument.mutateAsync({
        instrument_code: newCode,
        instrument_name: newName,
        serial_number: newSerial || `SN-${Math.floor(Math.random() * 900000)}`,
        asset_tag: newAssetTag || `AT-${Math.floor(Math.random() * 90000)}`,
        manufacturer: newManufacturer || 'Unknown',
        model: newModel || 'Unknown',
        operational_status: 'operational',
        availability_status: 'available',
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        metadata_json: {
          instrument_type: newType,
          location: newLocation,
          next_calibration_date: newCalibDue,
          notes: newNotes,
          active_session: null,
          usage_log: [],
        },
      });
      resetModal();
    } catch (err) { console.error(err); }
  };

  const resetModal = () => {
    setShowModal(false); setStep(1);
    setNewName(''); setNewCode(`INS-${Math.floor(1000 + Math.random() * 9000)}`);
    setNewSerial(''); setNewAssetTag(''); setNewManufacturer('');
    setNewModel(''); setNewLocation(''); setNewCalibDue(''); setNewNotes('');
  };

  const formatSessionTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch { return iso; }
  };

  const getCalibStatus = (ins: any) => {
    const due = ins.metadata_json?.next_calibration_date;
    if (!due) return null;
    const daysLeft = Math.round((new Date(due).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return daysLeft;
  };

  return (
    <div className="p-5 space-y-5 bg-slate-50 min-h-full">

      {/* ── KPI Bar ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Instruments', value: total, sub: 'Registered assets', gradient: 'from-slate-600 to-slate-800', icon: <Microscope className="w-5 h-5" /> },
          { label: 'Operational', value: operational, sub: 'Ready to use', gradient: 'from-emerald-500 to-teal-600', icon: <CheckCircle2 className="w-5 h-5" /> },
          { label: 'In Use / Booked', value: inUseCount, sub: isAdminOrPI ? 'Click to view who' : 'Currently occupied', gradient: inUseCount > 0 ? 'from-blue-500 to-indigo-600' : 'from-slate-400 to-slate-600', icon: <Users className="w-5 h-5" /> },
          { label: 'Maintenance / OOS', value: inMaintenance + outOfService, sub: inMaintenance + outOfService > 0 ? 'Action required' : 'All operational', gradient: inMaintenance + outOfService > 0 ? 'from-rose-500 to-rose-700' : 'from-slate-400 to-slate-600', icon: <Wrench className="w-5 h-5" /> },
        ].map(k => (
          <div key={k.label} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className={`bg-gradient-to-br ${k.gradient} p-4 flex items-center justify-between`}>
              <div className="text-white/80">{k.icon}</div>
              <span className="text-3xl font-black text-white">{k.value}</span>
            </div>
            <div className="px-4 py-3">
              <p className="text-xs font-bold text-slate-700">{k.label}</p>
              <p className="text-[10px] text-slate-400 mt-0.5">{k.sub}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Admin/PI: Active Usage Sessions Panel ────────── */}
      {isAdminOrPI && activeUsageSessions.length > 0 && (
        <div className="bg-white rounded-2xl border border-blue-200 shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <h3 className="text-sm font-black text-white">Live Usage Dashboard</h3>
              <span className="text-blue-100 text-xs">(Admin / PI View)</span>
            </div>
            <span className="text-xs font-bold bg-white/20 text-white px-2.5 py-1 rounded-full">
              {activeUsageSessions.length} active session{activeUsageSessions.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {activeUsageSessions.map(({ instrument, session }) => (
              <div key={instrument.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-slate-50/80 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Cpu className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">{instrument.instrument_name}</p>
                    <p className="text-[10px] text-slate-400 font-mono">{instrument.instrument_code}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  {/* Researcher using it */}
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-indigo-100 rounded-full flex items-center justify-center">
                      <User2 className="w-4 h-4 text-indigo-600" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-700">{session.user_name || 'Unknown Researcher'}</p>
                      <p className="text-[10px] text-slate-400">{session.user_role || 'Researcher'}</p>
                    </div>
                  </div>

                  {/* Experiment */}
                  {session.experiment_title && (
                    <div className="hidden md:flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                      <span className="text-[10px] text-slate-500 max-w-[160px] truncate">{session.experiment_title}</span>
                    </div>
                  )}

                  {/* Time started */}
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <div>
                      <p className="text-[10px] font-semibold text-slate-600">{session.started_at ? formatSessionTime(session.started_at) : 'Now'}</p>
                      <p className="text-[10px] text-slate-400">
                        {session.expected_end ? `Until ${formatSessionTime(session.expected_end)}` : 'Open-ended'}
                      </p>
                    </div>
                  </div>

                  <span className="hidden sm:flex items-center gap-1 text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
                    LIVE
                  </span>
                </div>

                <button
                  onClick={() => onSelectInstrument(instrument.id)}
                  className="text-[10px] font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer ml-4"
                >
                  <Eye className="w-3.5 h-3.5" />
                  Details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Search + Filters ─────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search by instrument code, name, manufacturer, serial…"
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          {!isViewer && (
            <button
              onClick={() => { setShowModal(true); setStep(1); }}
              className="flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              Add Instrument
            </button>
          )}
        </div>

        {/* Operational status filter */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Status</span>
          <button onClick={() => setOpFilter('')}
            className={`text-xs font-semibold px-2.5 py-1 rounded-lg border cursor-pointer transition-all ${opFilter === '' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
            All
          </button>
          {Object.entries(OP_STATUS).map(([key, cfg]) => (
            <button key={key} onClick={() => setOpFilter(opFilter === key ? '' : key)}
              className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg border cursor-pointer transition-all ${
                opFilter === key ? `${cfg.bg} ${cfg.color} ${cfg.border}` : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}>
              <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
              {cfg.label}
            </button>
          ))}
        </div>

        {/* Availability filter */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Availability</span>
          <button onClick={() => setAvailFilter('')}
            className={`text-xs font-semibold px-2.5 py-1 rounded-lg border cursor-pointer transition-all ${availFilter === '' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
            All
          </button>
          {Object.entries(AVAIL_STATUS).map(([key, cfg]) => (
            <button key={key} onClick={() => setAvailFilter(availFilter === key ? '' : key)}
              className={`text-xs font-semibold px-2.5 py-1 rounded-lg border cursor-pointer transition-all ${
                availFilter === key ? `${cfg.bg} ${cfg.color} border-current` : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}>
              {cfg.label}
            </button>
          ))}
        </div>

        {/* Type filter chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Type</span>
          {INSTRUMENT_TYPES.map(t => (
            <button key={t.code} onClick={() => setTypeFilter(typeFilter === t.code ? '' : t.code)}
              className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg border cursor-pointer transition-all ${
                typeFilter === t.code ? 'bg-amber-50 text-amber-700 border-amber-400' : 'bg-white text-slate-600 border-slate-200 hover:bg-amber-50 hover:border-amber-300'
              }`}>
              <span>{t.icon}</span>{t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Instruments Table ─────────────────────────────── */}
      {isLoading ? (
        <div className="flex flex-col justify-center p-16 items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
          <span className="text-xs text-slate-400 font-medium">Loading instrument registry…</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-16 text-rose-500 gap-3">
          <AlertCircle className="w-8 h-8" />
          <span className="font-semibold text-sm">Failed to load instruments.</span>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-600">{displayItems.length} instrument{displayItems.length !== 1 ? 's' : ''}</span>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Filter className="w-3.5 h-3.5" />
                Filters: {[opFilter, availFilter, typeFilter, searchQuery].filter(Boolean).length}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-100">
                  <tr>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Instrument</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Manufacturer / Model</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Asset / Serial</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Op. Status</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Currently In Use By</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Calibration</th>
                    <th className="py-3 px-4 text-right font-bold uppercase tracking-wide text-[10px]">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 font-medium">
                  {displayItems.map((ins) => {
                    const opCfg = OP_STATUS[ins.operational_status] || OP_STATUS.operational;
                    const availCfg = AVAIL_STATUS[ins.availability_status] || AVAIL_STATUS.available;
                    const session = getActiveSession(ins);
                    const calibDays = getCalibStatus(ins);
                    const typeInfo = INSTRUMENT_TYPES.find(t => t.code === ins.metadata_json?.instrument_type) || INSTRUMENT_TYPES[0];
                    const isInUse = ins.availability_status === 'in_use' || ins.availability_status === 'booked';

                    return (
                      <tr key={ins.id} className="hover:bg-slate-50/80 transition-colors group">
                        {/* Instrument name */}
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2.5">
                            <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-base ${isInUse ? 'bg-blue-100' : 'bg-slate-100'}`}>
                              {typeInfo.icon}
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${opCfg.dot} ${isInUse ? 'animate-pulse' : ''}`} />
                                <span className="font-bold text-slate-800">{ins.instrument_name}</span>
                              </div>
                              <span className="font-mono text-[10px] text-amber-600 font-bold">{ins.instrument_code}</span>
                            </div>
                          </div>
                        </td>

                        {/* Manufacturer */}
                        <td className="py-4 px-4">
                          <p className="font-semibold text-slate-700">{ins.manufacturer}</p>
                          <p className="text-[10px] text-slate-400">{ins.model}</p>
                        </td>

                        {/* Asset / Serial */}
                        <td className="py-4 px-4">
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-1 text-[10px]">
                              <Tag className="w-3 h-3 text-slate-400" />
                              <span className="font-mono text-slate-600">{ins.asset_tag || '—'}</span>
                            </div>
                            <div className="flex items-center gap-1 text-[10px]">
                              <Settings className="w-3 h-3 text-slate-400" />
                              <span className="font-mono text-slate-500">{ins.serial_number || '—'}</span>
                            </div>
                            {ins.metadata_json?.location && (
                              <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-[120px]">📍 {ins.metadata_json.location}</div>
                            )}
                          </div>
                        </td>

                        {/* Op Status */}
                        <td className="py-4 px-4">
                          <div className="space-y-1">
                            <span className={`inline-flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1 rounded-lg border ${opCfg.bg} ${opCfg.color} ${opCfg.border}`}>
                              <span className={`w-2 h-2 rounded-full ${opCfg.dot}`} />
                              {opCfg.label}
                            </span>
                            <div>
                              <span className={`inline-flex text-[10px] font-semibold px-2 py-0.5 rounded-full ${availCfg.bg} ${availCfg.color}`}>
                                {availCfg.label}
                              </span>
                            </div>
                          </div>
                        </td>

                        {/* Who's using it */}
                        <td className="py-4 px-4">
                          {isInUse && session ? (
                            <div className="flex items-center gap-2">
                              <div className="w-7 h-7 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <User2 className="w-4 h-4 text-indigo-600" />
                              </div>
                              <div>
                                <p className="text-xs font-bold text-slate-800">{session.user_name || 'Researcher'}</p>
                                <p className="text-[10px] text-slate-400">
                                  {session.started_at ? `Since ${formatSessionTime(session.started_at)}` : 'Active now'}
                                </p>
                                {session.experiment_title && (
                                  <p className="text-[10px] text-indigo-600 truncate max-w-[120px]">↳ {session.experiment_title}</p>
                                )}
                              </div>
                            </div>
                          ) : ins.availability_status === 'reserved' && session ? (
                            <div className="flex items-center gap-2">
                              <div className="w-7 h-7 bg-violet-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <Calendar className="w-4 h-4 text-violet-600" />
                              </div>
                              <div>
                                <p className="text-xs font-bold text-violet-700">Reserved</p>
                                <p className="text-[10px] text-slate-400">{session.user_name || '—'}</p>
                                <p className="text-[10px] text-slate-400">{session.started_at ? formatSessionTime(session.started_at) : ''}</p>
                              </div>
                            </div>
                          ) : (
                            <span className="text-[10px] text-slate-400 italic">— Free to use —</span>
                          )}
                        </td>

                        {/* Calibration */}
                        <td className="py-4 px-4">
                          {calibDays !== null ? (
                            <div>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                calibDays < 0 ? 'bg-rose-100 text-rose-700' :
                                calibDays < 14 ? 'bg-amber-100 text-amber-700' :
                                'bg-slate-100 text-slate-600'
                              }`}>
                                {calibDays < 0 ? `${Math.abs(calibDays)}d OVERDUE` : calibDays === 0 ? 'DUE TODAY' : `${calibDays}d left`}
                              </span>
                            </div>
                          ) : (
                            <span className="text-[10px] text-slate-400">Not scheduled</span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-1.5 justify-end">
                            {!isViewer && ins.operational_status === 'operational' && !isInUse && (
                              <button
                                onClick={() => setBookModal({ id: ins.id, name: ins.instrument_name, code: ins.instrument_code })}
                                className="flex items-center gap-1 bg-blue-50 hover:bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-1.5 rounded-lg border border-blue-200 transition-all cursor-pointer"
                              >
                                <Calendar className="w-3 h-3" />
                                Book
                              </button>
                            )}
                            <button
                              onClick={() => onSelectInstrument(ins.id)}
                              className="flex items-center gap-1 bg-amber-50 hover:bg-amber-100 text-amber-700 text-[10px] font-bold px-2 py-1.5 rounded-lg border border-amber-200 transition-all cursor-pointer"
                            >
                              Detail
                              <ArrowUpRight className="w-3 h-3" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {displayItems.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-16 text-center">
                        <div className="flex flex-col items-center gap-3 text-slate-400">
                          <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center">
                            <Microscope className="w-6 h-6" />
                          </div>
                          <div>
                            <p className="font-semibold text-slate-600">No instruments found</p>
                            <p className="text-xs mt-1">Adjust filters or register a new instrument.</p>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {instrumentData && instrumentData.total_pages > 1 && (
            <div className="flex justify-center items-center gap-3">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl disabled:opacity-40 hover:bg-slate-50 cursor-pointer shadow-sm">
                ← Previous
              </button>
              <span className="text-xs text-slate-500 font-bold bg-white border border-slate-200 px-4 py-2 rounded-xl shadow-sm">
                Page {page} of {instrumentData.total_pages}
              </span>
              <button disabled={page >= instrumentData.total_pages} onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl disabled:opacity-40 hover:bg-slate-50 cursor-pointer shadow-sm">
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* ── Book / Use Now Modal ─────────────────────────── */}
      {bookModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-md shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-5 flex items-center justify-between">
              <div>
                <h3 className="text-base font-black text-white">Book Instrument</h3>
                <p className="text-blue-100 text-xs mt-0.5 truncate max-w-[280px]">{bookModal.name} · {bookModal.code}</p>
              </div>
              <button onClick={() => setBookModal(null)} className="text-white/70 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              {/* Book mode tabs */}
              <div className="flex rounded-xl overflow-hidden border border-slate-200">
                <button
                  type="button"
                  onClick={() => setBookMode('use_now')}
                  className={`flex-1 py-2 text-xs font-bold transition-all cursor-pointer ${bookMode === 'use_now' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
                >
                  ▶ Use Now
                </button>
                <button
                  type="button"
                  onClick={() => setBookMode('reserve')}
                  className={`flex-1 py-2 text-xs font-bold transition-all cursor-pointer ${bookMode === 'reserve' ? 'bg-indigo-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
                >
                  📅 Reserve for Later
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Start Time</label>
                  <input type="datetime-local" value={bookDate} onChange={e => setBookDate(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Expected End</label>
                  <input type="datetime-local" value={bookEndDate} onChange={e => setBookEndDate(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Experiment / Project (Optional)</label>
                <input type="text" value={bookExperiment} onChange={e => setBookExperiment(e.target.value)}
                  placeholder="e.g. CRISPR Screen — Round 3 Validation"
                  className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Notes</label>
                <textarea value={bookNotes} onChange={e => setBookNotes(e.target.value)} rows={2}
                  placeholder="Any special requirements or setup notes…"
                  className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700 font-medium">
                📋 This booking will be logged under your name and visible to Admin and PI for oversight.
              </div>

              <div className="flex justify-end gap-3">
                <button onClick={() => setBookModal(null)} className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">Cancel</button>
                <button
                  onClick={() => {
                    // In a real integration this calls an API to update instrument availability + log session
                    alert(`Booking confirmed for ${bookModal.name}\nMode: ${bookMode}\nResearcher: ${user?.first_name || user?.username}\nExperiment: ${bookExperiment || 'N/A'}`);
                    setBookModal(null);
                    setBookExperiment(''); setBookNotes(''); setBookEndDate('');
                  }}
                  className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl shadow-sm cursor-pointer"
                >
                  <Check className="w-4 h-4" />
                  {bookMode === 'use_now' ? 'Start Using Now' : 'Confirm Reservation'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── New Instrument Multi-Step Modal ──────────────── */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            <div className="bg-gradient-to-r from-amber-500 to-orange-600 p-5 flex items-center justify-between flex-shrink-0">
              <div>
                <h3 className="text-base font-black text-white">Register New Instrument</h3>
                <p className="text-amber-100 text-xs mt-0.5">
                  Step {step} of 3 — {step === 1 ? 'Identity & Type' : step === 2 ? 'Specs & Location' : 'Review & Confirm'}
                </p>
              </div>
              <button onClick={resetModal} className="text-white/70 hover:text-white cursor-pointer"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex flex-shrink-0">
              {[1, 2, 3].map(s => <div key={s} className={`flex-1 h-1 ${s <= step ? 'bg-amber-500' : 'bg-slate-100'}`} />)}
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 overflow-y-auto">
              {/* Step 1 */}
              {step === 1 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Instrument Code</label>
                      <input type="text" required value={newCode} onChange={e => setNewCode(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500 font-mono" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Instrument Name <span className="text-rose-500">*</span></label>
                      <input type="text" required value={newName} onChange={e => setNewName(e.target.value)}
                        placeholder="e.g. Zeiss Axio Observer Z1" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">Instrument Type</label>
                    <div className="grid grid-cols-4 gap-2">
                      {INSTRUMENT_TYPES.filter(t => t.code).map(t => (
                        <button key={t.code} type="button" onClick={() => setNewType(t.code)}
                          className={`flex flex-col items-center gap-1 p-2.5 rounded-xl text-[10px] font-semibold border-2 transition-all cursor-pointer ${
                            newType === t.code ? 'bg-amber-50 text-amber-700 border-amber-400' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                          }`}>
                          <span className="text-xl">{t.icon}</span>
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2 */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Manufacturer</label>
                      <input type="text" value={newManufacturer} onChange={e => setNewManufacturer(e.target.value)}
                        placeholder="e.g. Zeiss, Thermo, Beckman" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Model</label>
                      <input type="text" value={newModel} onChange={e => setNewModel(e.target.value)}
                        placeholder="e.g. Axio Observer Z1" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Serial Number</label>
                      <input type="text" value={newSerial} onChange={e => setNewSerial(e.target.value)}
                        placeholder="e.g. ZSS-2024-001" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500 font-mono" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Asset Tag</label>
                      <input type="text" value={newAssetTag} onChange={e => setNewAssetTag(e.target.value)}
                        placeholder="e.g. AT-10042" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500 font-mono" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Lab Location</label>
                      <input type="text" value={newLocation} onChange={e => setNewLocation(e.target.value)}
                        placeholder="e.g. Lab B - Room 204" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Next Calibration Date</label>
                      <input type="date" value={newCalibDue} onChange={e => setNewCalibDue(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">Notes / Special Instructions</label>
                    <textarea value={newNotes} onChange={e => setNewNotes(e.target.value)} rows={2}
                      placeholder="Warm-up time, booking constraints, safety notes…"
                      className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500 resize-none" />
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 flex items-start gap-2">
                    <Users className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-blue-700 font-medium">
                      Usage tracking will be automatically enabled. Admin and PI can monitor who is using this instrument in real-time from the Live Usage Dashboard.
                    </p>
                  </div>
                </div>
              )}

              {/* Step 3 — Review */}
              {step === 3 && (
                <div className="space-y-4">
                  <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5 space-y-2.5">
                    <h4 className="text-xs font-black text-slate-700 uppercase tracking-wider mb-3">Review Instrument Details</h4>
                    {[
                      { label: 'Code', value: newCode },
                      { label: 'Name', value: newName },
                      { label: 'Type', value: INSTRUMENT_TYPES.find(t => t.code === newType)?.label || newType },
                      { label: 'Manufacturer', value: newManufacturer || '—' },
                      { label: 'Model', value: newModel || '—' },
                      { label: 'Serial', value: newSerial || 'Auto-generated' },
                      { label: 'Asset Tag', value: newAssetTag || 'Auto-generated' },
                      { label: 'Location', value: newLocation || '—' },
                      { label: 'Next Calibration', value: newCalibDue || 'Not scheduled' },
                    ].map(row => (
                      <div key={row.label} className="flex items-center justify-between text-xs border-b border-slate-200 pb-2 last:border-0 last:pb-0">
                        <span className="text-slate-500 font-medium">{row.label}</span>
                        <span className="font-bold text-slate-800">{row.value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-amber-700 font-medium">
                      Instrument will be registered as <strong>Operational / Available</strong>. Bookings and usage sessions will be tracked from this point forward.
                    </p>
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="flex justify-between items-center pt-2 border-t border-slate-100">
                <button type="button" onClick={() => step > 1 ? setStep(s => s - 1) : resetModal()}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">
                  {step > 1 ? '← Back' : 'Cancel'}
                </button>
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    {[1, 2, 3].map(s => <div key={s} className={`w-2 h-2 rounded-full ${s === step ? 'bg-amber-500' : 'bg-slate-200'}`} />)}
                  </div>
                  {step < 3 ? (
                    <button type="button" onClick={() => setStep(s => s + 1)} disabled={step === 1 && !newName.trim()}
                      className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-amber-500 hover:bg-amber-600 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                      Continue <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button type="submit" disabled={createInstrument.isPending}
                      className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                      {createInstrument.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      {createInstrument.isPending ? 'Registering…' : 'Register Instrument'}
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
