import React, { useState, useMemo } from 'react';
import type { ViewMode } from '../../types';
import {
  Search, Plus, ArrowUpRight, MapPin, Loader2, AlertCircle,
  FlaskConical, Dna, Thermometer, ChevronRight, X, Check,
  BarChart3, Clock, PackageCheck, AlertTriangle, Filter,
  TestTube, Atom, Tag, QrCode
} from 'lucide-react';
import { useSamples, useCreateSample } from '../../hooks/useSamples';
import { useExperiments } from '../../hooks/useExperiments';
import { useAuth } from '../../providers/AuthProvider';
import { isStrictlyViewer } from '../../utils/permissions';

interface SampleRegistryViewProps {
  onSelectSample: (sampleId: string) => void;
  onSelectView: (view: ViewMode) => void;
}

const SAMPLE_TYPES = [
  { code: 'CELL_LINE', label: 'Cell Line', color: 'bg-violet-100 text-violet-700', icon: '🧫' },
  { code: 'PLASMID', label: 'Plasmid', color: 'bg-blue-100 text-blue-700', icon: '🧬' },
  { code: 'REAGENT', label: 'Reagent', color: 'bg-amber-100 text-amber-700', icon: '⚗️' },
  { code: 'PROTEIN', label: 'Protein', color: 'bg-emerald-100 text-emerald-700', icon: '🔬' },
  { code: 'RNA', label: 'RNA Sample', color: 'bg-pink-100 text-pink-700', icon: '🧪' },
  { code: 'TISSUE', label: 'Tissue', color: 'bg-rose-100 text-rose-700', icon: '🫀' },
];

const TEMPS = [
  { code: '', label: 'All Temps' },
  { code: '-196C', label: '-196°C (LN₂)' },
  { code: '-80C', label: '-80°C (ULT)' },
  { code: '-20C', label: '-20°C' },
  { code: '4C', label: '4°C (Fridge)' },
  { code: 'RT', label: 'Room Temp' },
];

const STATUS_COLORS: Record<string, string> = {
  available: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  consumed: 'bg-slate-100 text-slate-600 border-slate-200',
  expired: 'bg-rose-100 text-rose-700 border-rose-200',
  quarantine: 'bg-amber-100 text-amber-700 border-amber-200',
};

export const SampleRegistryView: React.FC<SampleRegistryViewProps> = ({
  onSelectSample,
  onSelectView
}) => {
  const { user } = useAuth();
  const isViewer = isStrictlyViewer(user);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [typeCode, setTypeCode] = useState<string>('CELL_LINE');
  const [qty, setQty] = useState('');
  const [unit, setUnit] = useState('vials');
  const [storageTemp, setStorageTemp] = useState('-80C');
  const [locationString, setLocationString] = useState('Freezer ULT-01 — Rack A, Box 01');
  const [notes, setNotes] = useState('');
  const [sampleCode, setSampleCode] = useState(`SMP-${Math.floor(1000 + Math.random() * 9000)}`);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string>('');

  const { data: samplesData, isLoading, error } = useSamples(
    page,
    pageSize,
    undefined,
    selectedStatus ? selectedStatus : undefined,
    searchQuery
  );

  const createSample = useCreateSample();
  const { data: experimentsData } = useExperiments(1, 100);

  // KPI derivations
  const total = samplesData?.total ?? 0;
  const available = samplesData?.items.filter(s => s.status === 'available').length ?? 0;
  const consumed = samplesData?.items.filter(s => s.status === 'consumed').length ?? 0;
  const expired = samplesData?.items.filter(s => s.status === 'expired').length ?? 0;

  const statuses = [
    { label: 'All', value: '' },
    { label: 'Available', value: 'available' },
    { label: 'Consumed', value: 'consumed' },
    { label: 'Expired', value: 'expired' },
  ];

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !selectedExperimentId) return;
    try {
      await createSample.mutateAsync({
        sample_code: sampleCode,
        barcode: `QR-${Math.floor(1000000 + Math.random() * 9000000)}`,
        sample_name: name,
        status: 'available',
        quantity: parseFloat(qty) || 1,
        unit,
        storage_temperature: storageTemp,
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        experiment_id: selectedExperimentId,
        metadata_json: { typeCode, locationString, notes }
      });
      resetModal();
    } catch (err) {
      console.error('Failed to create sample:', err);
    }
  };

  const resetModal = () => {
    setName(''); setQty(''); setNotes(''); setStep(1);
    setSampleCode(`SMP-${Math.floor(1000 + Math.random() * 9000)}`);
    setShowModal(false);
  };

  const getTypeInfo = (code: string) =>
    SAMPLE_TYPES.find(t => t.code === code) || { code, label: code, color: 'bg-slate-100 text-slate-700', icon: '🔬' };

  const getTempColor = (temp: string) => {
    if (temp?.includes('-196')) return 'text-indigo-600 bg-indigo-50';
    if (temp?.includes('-80')) return 'text-blue-600 bg-blue-50';
    if (temp?.includes('-20')) return 'text-cyan-600 bg-cyan-50';
    if (temp?.includes('4')) return 'text-teal-600 bg-teal-50';
    return 'text-slate-500 bg-slate-50';
  };

  // Filter by type locally (type is in metadata_json)
  const displayItems = useMemo(() => {
    if (!samplesData?.items) return [];
    if (!selectedType) return samplesData.items;
    return samplesData.items.filter(s => s.metadata_json?.typeCode === selectedType);
  }, [samplesData, selectedType]);

  return (
    <div className="p-5 space-y-5 bg-slate-50 min-h-full">

      {/* ── KPI Bar ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Registered',
            value: total,
            icon: <TestTube className="w-5 h-5" />,
            color: 'from-blue-600 to-indigo-600',
            sub: `Page ${page} of ${samplesData?.total_pages ?? 1}`,
          },
          {
            label: 'Available',
            value: available,
            icon: <PackageCheck className="w-5 h-5" />,
            color: 'from-emerald-500 to-teal-600',
            sub: total > 0 ? `${Math.round((available / (samplesData?.items.length || 1)) * 100)}% this page` : 'No data',
          },
          {
            label: 'Consumed',
            value: consumed,
            icon: <FlaskConical className="w-5 h-5" />,
            color: 'from-slate-500 to-slate-700',
            sub: 'This page',
          },
          {
            label: 'Expired / Issues',
            value: expired,
            icon: <AlertTriangle className="w-5 h-5" />,
            color: expired > 0 ? 'from-rose-500 to-rose-700' : 'from-slate-400 to-slate-600',
            sub: expired > 0 ? 'Attention required' : 'All clear',
          },
        ].map(k => (
          <div key={k.label} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className={`bg-gradient-to-br ${k.color} p-4 flex items-center justify-between`}>
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

      {/* ── Search + Filters ────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search by sample ID, barcode, or name…"
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1">Status</span>
            {statuses.map(st => (
              <button
                key={st.value}
                onClick={() => { setSelectedStatus(st.value); setPage(1); }}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-all whitespace-nowrap cursor-pointer border ${
                  selectedStatus === st.value
                    ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-teal-300 hover:bg-teal-50'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {!isViewer && (
            <button
              onClick={() => { setShowModal(true); setStep(1); }}
              className="flex items-center gap-2 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              Register Sample
            </button>
          )}
        </div>

        {/* Type filter chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Type</span>
          <button
            onClick={() => setSelectedType('')}
            className={`text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
              selectedType === '' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            All
          </button>
          {SAMPLE_TYPES.map(t => (
            <button
              key={t.code}
              onClick={() => setSelectedType(t.code)}
              className={`text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1 ${
                selectedType === t.code ? `${t.color} border-current` : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Table ───────────────────────────────────────────────── */}
      {isLoading ? (
        <div className="flex flex-col justify-center p-16 items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
          <span className="text-xs text-slate-400 font-medium">Loading sample registry…</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-16 text-rose-500 gap-3">
          <AlertCircle className="w-8 h-8" />
          <span className="font-semibold text-sm">Failed to load samples.</span>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-600">
                {displayItems.length} sample{displayItems.length !== 1 ? 's' : ''}
                {selectedType && ` · ${getTypeInfo(selectedType).label}`}
                {selectedStatus && ` · ${selectedStatus}`}
              </span>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Filter className="w-3.5 h-3.5" />
                Active filters: {[selectedStatus, selectedType, searchQuery].filter(Boolean).length}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                  <tr>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Sample ID</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Name</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Type</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Storage</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Quantity</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Status</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Registered</th>
                    <th className="py-3 px-4 text-right font-bold uppercase tracking-wide text-[10px]">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 font-medium">
                  {displayItems.map((s) => {
                    const typeInfo = getTypeInfo(s.metadata_json?.typeCode || 'UNKNOWN');
                    const tempClass = getTempColor(s.storage_temperature || '');
                    const locStr = s.metadata_json?.locationString || 'Unassigned';
                    return (
                      <tr key={s.id} className="hover:bg-slate-50/80 transition-colors group">
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                              s.status === 'available' ? 'bg-emerald-400' :
                              s.status === 'expired' ? 'bg-rose-400' : 'bg-slate-300'
                            }`} />
                            <span className="font-mono font-bold text-blue-600">{s.sample_code}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono pl-4 mt-0.5">{s.barcode}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="text-slate-800 font-semibold">{s.sample_name}</span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold border ${typeInfo.color}`}>
                            <span>{typeInfo.icon}</span>
                            {typeInfo.label}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-start gap-1.5">
                            <Thermometer className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${tempClass.split(' ')[0]}`} />
                            <div>
                              <div className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${tempClass}`}>
                                {s.storage_temperature || 'N/A'}
                              </div>
                              <div className="text-[10px] text-slate-400 mt-0.5 max-w-[140px] truncate flex items-center gap-1">
                                <MapPin className="w-3 h-3 flex-shrink-0" />
                                {locStr}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="font-bold text-slate-800">{s.quantity}</span>
                          <span className="text-slate-400 ml-1">{s.unit}</span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${STATUS_COLORS[s.status] || 'bg-slate-100 text-slate-600 border-slate-200'}`}>
                            {s.status === 'available' ? '● ' : ''}{s.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-400 text-[10px]">
                          {new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2 justify-end">
                            <button
                              onClick={() => onSelectSample(s.id)}
                              className="flex items-center gap-1 bg-teal-50 hover:bg-teal-100 text-teal-700 text-[10px] font-bold px-2.5 py-1.5 rounded-lg border border-teal-200 transition-all cursor-pointer group-hover:shadow-sm"
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
                      <td colSpan={8} className="py-16 text-center">
                        <div className="flex flex-col items-center gap-3 text-slate-400">
                          <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center">
                            <FlaskConical className="w-6 h-6" />
                          </div>
                          <div>
                            <p className="font-semibold text-slate-600">No samples found</p>
                            <p className="text-xs mt-1">Try adjusting your filters or register a new sample.</p>
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
          {samplesData && samplesData.total_pages > 1 && (
            <div className="flex justify-center items-center gap-3">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl disabled:opacity-40 hover:bg-slate-50 cursor-pointer shadow-sm"
              >
                ← Previous
              </button>
              <span className="text-xs text-slate-500 font-bold bg-white border border-slate-200 px-4 py-2 rounded-xl shadow-sm">
                Page {page} of {samplesData.total_pages}
              </span>
              <button
                disabled={page >= samplesData.total_pages}
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl disabled:opacity-40 hover:bg-slate-50 cursor-pointer shadow-sm"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* ── Multi-Step Registration Modal ────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden">
            {/* Modal header */}
            <div className="bg-gradient-to-r from-teal-600 to-emerald-600 p-6 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-black text-white">Register Biological / Chemical Sample</h3>
                <p className="text-teal-100 text-xs mt-0.5">Step {step} of 3 — {step === 1 ? 'Identity & Type' : step === 2 ? 'Storage & Quantity' : 'Review & Submit'}</p>
              </div>
              <button onClick={resetModal} className="text-white/70 hover:text-white transition-colors cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Step indicators */}
            <div className="flex border-b border-slate-100">
              {[1, 2, 3].map(s => (
                <div key={s} className={`flex-1 h-1 ${s <= step ? 'bg-teal-500' : 'bg-slate-100'}`} />
              ))}
            </div>

            <form onSubmit={handleAddSubmit} className="p-6 space-y-5">
              {/* Step 1: Identity & Type */}
              {step === 1 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Sample Code <span className="text-rose-500">*</span></label>
                      <input
                        type="text"
                        required
                        value={sampleCode}
                        onChange={(e) => setSampleCode(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500 font-mono text-slate-600 bg-slate-50"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Sample Name <span className="text-rose-500">*</span></label>
                      <input
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g. HEK293T Cell Line — Passage 14"
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">Sample Type <span className="text-rose-500">*</span></label>
                    <div className="grid grid-cols-3 gap-2">
                      {SAMPLE_TYPES.map(t => (
                        <button
                          key={t.code}
                          type="button"
                          onClick={() => setTypeCode(t.code)}
                          className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold border-2 transition-all cursor-pointer ${
                            typeCode === t.code ? `${t.color} border-current shadow-sm` : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                          }`}
                        >
                          <span className="text-base">{t.icon}</span>
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">Linked Experiment <span className="text-rose-500">*</span></label>
                    <select
                      required
                      value={selectedExperimentId}
                      onChange={(e) => setSelectedExperimentId(e.target.value)}
                      className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500 bg-white"
                    >
                      <option value="" disabled>Select an Experiment…</option>
                      {experimentsData?.items.map(exp => (
                        <option key={exp.id} value={exp.id}>{exp.title}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Step 2: Storage & Quantity */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Quantity</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={qty}
                        onChange={(e) => setQty(e.target.value)}
                        placeholder="e.g. 5"
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Unit</label>
                      <select
                        value={unit}
                        onChange={(e) => setUnit(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500 bg-white"
                      >
                        <option value="vials">Vials</option>
                        <option value="mL">mL</option>
                        <option value="µL">µL</option>
                        <option value="mg">mg</option>
                        <option value="µg">µg</option>
                        <option value="ng">ng</option>
                        <option value="units">Units</option>
                        <option value="aliquots">Aliquots</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">Storage Temperature</label>
                    <div className="grid grid-cols-3 gap-2">
                      {TEMPS.filter(t => t.code).map(t => (
                        <button
                          key={t.code}
                          type="button"
                          onClick={() => setStorageTemp(t.code)}
                          className={`px-3 py-2 rounded-xl text-xs font-semibold border-2 transition-all cursor-pointer ${
                            storageTemp === t.code
                              ? 'border-blue-500 bg-blue-50 text-blue-700'
                              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                          }`}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">Storage Location</label>
                    <input
                      type="text"
                      value={locationString}
                      onChange={(e) => setLocationString(e.target.value)}
                      placeholder="e.g. Freezer ULT-01 — Rack A, Box 02"
                      className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">Notes</label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Special handling instructions, passage number, lot details…"
                      rows={3}
                      className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-teal-500 resize-none"
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Review */}
              {step === 3 && (
                <div className="space-y-4">
                  <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5 space-y-3">
                    <h4 className="text-xs font-black text-slate-700 uppercase tracking-wider">Review Sample Details</h4>
                    {[
                      { label: 'Code', value: sampleCode },
                      { label: 'Name', value: name },
                      { label: 'Type', value: getTypeInfo(typeCode).label },
                      { label: 'Temperature', value: storageTemp },
                      { label: 'Location', value: locationString },
                      { label: 'Quantity', value: `${qty || '–'} ${unit}` },
                    ].map(row => (
                      <div key={row.label} className="flex items-center justify-between text-xs border-b border-slate-200 pb-2 last:border-0 last:pb-0">
                        <span className="text-slate-500 font-medium">{row.label}</span>
                        <span className="font-bold text-slate-800">{row.value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="bg-teal-50 border border-teal-200 rounded-xl p-3 flex items-start gap-2">
                    <Check className="w-4 h-4 text-teal-600 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-teal-700 font-medium">This will register the sample in the chain of custody and generate a QR barcode.</p>
                  </div>
                </div>
              )}

              {/* Footer Buttons */}
              <div className="flex justify-between items-center pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => step > 1 ? setStep(s => s - 1) : resetModal()}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                >
                  {step > 1 ? '← Back' : 'Cancel'}
                </button>
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    {[1, 2, 3].map(s => (
                      <div key={s} className={`w-2 h-2 rounded-full ${s === step ? 'bg-teal-600' : 'bg-slate-200'}`} />
                    ))}
                  </div>
                  {step < 3 ? (
                    <button
                      type="button"
                      onClick={() => setStep(s => s + 1)}
                      disabled={step === 1 && (!name.trim() || !selectedExperimentId)}
                      className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-sm transition-colors cursor-pointer disabled:opacity-50"
                    >
                      Continue
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={createSample.isPending}
                      className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-xl shadow-sm transition-all cursor-pointer disabled:opacity-50"
                    >
                      {createSample.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      {createSample.isPending ? 'Registering…' : 'Confirm & Register'}
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
