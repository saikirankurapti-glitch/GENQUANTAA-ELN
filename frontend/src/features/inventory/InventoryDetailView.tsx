import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import {
  ArrowLeft, Loader2, AlertCircle, PackageMinus, PackagePlus,
  History, Droplets, CheckCircle2, AlertTriangle, Clock,
  MapPin, Tag, Truck, RefreshCw, X, Check, ShieldCheck,
  TrendingUp, TrendingDown, BarChart3, Info
} from 'lucide-react';
import { useInventoryItem, useReceiveInventory, useIssueInventory, useUpdateInventoryItem } from '../../hooks/useInventory';
import { useAuth } from '../../providers/AuthProvider';
import { isStrictlyViewer } from '../../utils/permissions';

interface InventoryDetailViewProps {
  inventoryId: string;
  onSelectView: (view: ViewMode) => void;
}

type WashStatus = 'clean' | 'needs_washing' | 'in_wash' | 'not_applicable';

const WASH_STATUS_CONFIG: Record<WashStatus, { label: string; color: string; bg: string; border: string; dot: string; icon: string }> = {
  clean: { label: 'Clean & Ready', color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', dot: 'bg-emerald-400', icon: '✓' },
  needs_washing: { label: 'Needs Washing', color: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200', dot: 'bg-rose-500', icon: '⚠' },
  in_wash: { label: 'In Wash Cycle', color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-400', icon: '🔄' },
  not_applicable: { label: 'Disposable / N/A', color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200', dot: 'bg-slate-300', icon: '—' },
};

const WASH_METHODS: Record<string, string> = {
  autoclave: 'Autoclave (121°C)',
  manual_hot: 'Manual Hot Wash',
  detergent_rinse: 'Detergent + DI Rinse',
  acid_wash: 'Acid Wash',
  ethanol_wipe: '70% EtOH Wipe',
  uv_sterilize: 'UV Sterilization',
  dishwasher: 'Lab Dishwasher',
  disposable: 'Disposable (N/A)',
};

export const InventoryDetailView: React.FC<InventoryDetailViewProps> = ({
  inventoryId,
  onSelectView,
}) => {
  const { user } = useAuth();
  const isViewer = isStrictlyViewer(user);

  const { data: item, isLoading, error } = useInventoryItem(inventoryId);
  const receiveInv = useReceiveInventory();
  const issueInv = useIssueInventory();
  const updateItem = useUpdateInventoryItem();

  const [receiveQty, setReceiveQty] = useState('');
  const [receiveLot, setReceiveLot] = useState('');
  const [issueQty, setIssueQty] = useState('');
  const [issueReason, setIssueReason] = useState('');
  const [activeAction, setActiveAction] = useState<'receive' | 'issue' | null>(null);

  // Wash status modal
  const [showWashModal, setShowWashModal] = useState(false);
  const [newWashStatus, setNewWashStatus] = useState<WashStatus>('clean');
  const [washNote, setWashNote] = useState('');

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center p-16 h-full items-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-rose-600" />
        <span className="text-xs text-slate-400 font-medium">Loading item details…</span>
      </div>
    );
  }

  if (error || !item || !(item as any).id) {
    return (
      <div className="flex flex-col items-center justify-center p-16 h-full gap-3 text-rose-500">
        <AlertCircle className="w-8 h-8" />
        <span className="font-semibold text-sm">Failed to load inventory item.</span>
        <button onClick={() => onSelectView('inventory')} className="text-xs text-slate-500 hover:underline cursor-pointer">
          ← Back to Inventory
        </button>
      </div>
    );
  }

  // ── Normalize all optional arrays & objects from API ──────────────────
  // The backend may return InventoryItemRead (flat) or InventoryItemDetail (with relations).
  // Nullish-coalesce every field that could be undefined or null.
  const itemAny = item as any;
  const transactions: any[] = Array.isArray(itemAny.transactions) ? itemAny.transactions : [];
  const batches: any[] = Array.isArray(itemAny.batches) ? itemAny.batches : [];
  const meta: Record<string, any> = (item.metadata_json && typeof item.metadata_json === 'object')
    ? item.metadata_json
    : {};

  // Wash status from metadata_json
  const washStatus: WashStatus = (meta.wash_status as WashStatus) || 'not_applicable';
  const wsCfg = WASH_STATUS_CONFIG[washStatus] || WASH_STATUS_CONFIG.not_applicable;
  const isReusable: boolean = Boolean(meta.is_reusable);
  const lastWashedAt: string | null = meta.last_washed_at ?? null;
  const lastWashedBy: string | null = meta.last_washed_by ?? null;
  const washMethod: string | null = meta.wash_method ?? null;

  // Stock gauge calculation
  const current = Number(item.current_stock ?? 0);
  const reorder = Number(item.reorder_level ?? 0);
  const minimum = Number(item.minimum_stock ?? 0);
  const maxDisplay = Math.max(reorder * 2.5, current * 1.2, 10);
  const pct = Math.min(100, Math.round((current / maxDisplay) * 100));
  const gaugeColor = current <= minimum ? '#ef4444' : current <= reorder ? '#f59e0b' : '#10b981';

  const handleReceive = async () => {
    if (!receiveQty) return;
    try {
      await receiveInv.mutateAsync({
        id: item.id,
        data: { quantity: parseFloat(receiveQty), lot_number: receiveLot || undefined, remarks: 'Received via detail view' }
      });
      setReceiveQty(''); setReceiveLot(''); setActiveAction(null);
    } catch (err) { console.error(err); }
  };

  const handleIssue = async () => {
    if (!issueQty) return;
    try {
      await issueInv.mutateAsync({
        id: item.id,
        data: { quantity: parseFloat(issueQty), remarks: issueReason || 'Issued via detail view' }
      });
      setIssueQty(''); setIssueReason(''); setActiveAction(null);
    } catch (err) { console.error(err); }
  };

  const handleUpdateWashStatus = async () => {
    try {
      const updatedMeta = {
        ...(item.metadata_json || {}),
        wash_status: newWashStatus,
        last_washed_at: newWashStatus === 'clean' ? new Date().toISOString() : (item.metadata_json?.last_washed_at || null),
        last_washed_by: newWashStatus === 'clean' ? (user?.first_name || user?.username || 'Unknown') : (item.metadata_json?.last_washed_by || null),
        wash_note: washNote,
      };
      await updateItem.mutateAsync({
        id: item.id,
        data: { metadata_json: updatedMeta }
      });
      setShowWashModal(false);
      setWashNote('');
    } catch (err) { console.error(err); }
  };

  const getTxColor = (type: string) => {
    if (type === 'receive') return { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', sign: '+', icon: <TrendingUp className="w-3.5 h-3.5 text-emerald-600" /> };
    if (type === 'issue' || type === 'consume') return { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', sign: '-', icon: <TrendingDown className="w-3.5 h-3.5 text-amber-600" /> };
    return { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-700', sign: '±', icon: <RefreshCw className="w-3.5 h-3.5 text-slate-500" /> };
  };

  return (
    <div className="p-5 space-y-5 bg-slate-50 min-h-full">

      {/* ── Header ──────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectView('inventory')}
            className="p-2 rounded-xl hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-rose-600 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-lg">
                {item.item_code}
              </span>
              {isReusable && (
                <span className="text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-200 px-2 py-0.5 rounded-lg">
                  ♻ Reusable
                </span>
              )}
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg border ${wsCfg.bg} ${wsCfg.color} ${wsCfg.border}`}>
                {wsCfg.icon} {wsCfg.label}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight mt-1">{item.item_name}</h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isViewer && (
            <>
              <button
                onClick={() => { setActiveAction('receive'); }}
                className="flex items-center gap-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-bold px-3.5 py-2 rounded-xl border border-emerald-200 transition-all cursor-pointer"
              >
                <PackagePlus className="w-4 h-4" />
                Receive Stock
              </button>
              <button
                onClick={() => { setActiveAction('issue'); }}
                className="flex items-center gap-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-bold px-3.5 py-2 rounded-xl border border-amber-200 transition-all cursor-pointer"
              >
                <PackageMinus className="w-4 h-4" />
                Issue / Consume
              </button>
              {isReusable && (
                <button
                  onClick={() => { setNewWashStatus(washStatus); setShowWashModal(true); }}
                  className={`flex items-center gap-1.5 text-xs font-bold px-3.5 py-2 rounded-xl border transition-all cursor-pointer ${washStatus === 'needs_washing'
                      ? 'bg-rose-600 text-white border-rose-600 hover:bg-rose-700 shadow-sm'
                      : 'bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200'
                    }`}
                >
                  <Droplets className="w-4 h-4" />
                  {washStatus === 'needs_washing' ? '⚠ Mark as Washed' : 'Update Wash Status'}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Wash Warning Banner ──────────────────────────── */}
      {washStatus === 'needs_washing' && (
        <div className="bg-rose-50 border-2 border-rose-300 rounded-2xl p-4 flex items-start gap-3">
          <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
          </div>
          <div className="flex-1">
            <p className="font-black text-rose-800 text-sm">⛔ DO NOT USE — Requires Washing Before Use</p>
            <p className="text-xs text-rose-700 mt-1">
              This item is marked as needing washing/sterilization. It must be properly cleaned using the designated method before it can be used in any experiment.
            </p>
            {washMethod && (
              <p className="text-xs font-bold text-rose-600 mt-1">Required method: {WASH_METHODS[washMethod] || washMethod}</p>
            )}
          </div>
        </div>
      )}

      {washStatus === 'in_wash' && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-amber-600 animate-spin flex-shrink-0" />
          <p className="text-sm font-bold text-amber-800">This item is currently in a wash cycle — do not remove until complete.</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* ── Left: Stock Gauge + Details ──────────────── */}
        <div className="lg:col-span-1 space-y-4">

          {/* Stock Gauge Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-wider mb-4">Stock Level</h3>

            {/* Big number */}
            <div className="text-center mb-4">
              <span className={`text-4xl font-black ${current <= minimum ? 'text-rose-600' : current <= reorder ? 'text-amber-600' : 'text-slate-800'}`}>
                {current}
              </span>
              <span className="text-slate-400 ml-2 text-lg font-semibold">{item.unit}</span>
              {item.is_low_stock && (
                <div className="mt-1">
                  <span className="text-[10px] font-black bg-rose-100 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full">
                    ⚠ LOW STOCK
                  </span>
                </div>
              )}
            </div>

            {/* Gauge bar */}
            <div className="space-y-2 mb-4">
              <div className="h-4 bg-slate-100 rounded-full overflow-hidden relative">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, backgroundColor: gaugeColor }}
                />
                {/* Minimum marker */}
                {minimum > 0 && (
                  <div
                    className="absolute top-0 h-full w-0.5 bg-rose-400 opacity-70"
                    style={{ left: `${Math.min(100, (minimum / maxDisplay) * 100)}%` }}
                    title={`Minimum: ${minimum}`}
                  />
                )}
                {/* Reorder marker */}
                {reorder > 0 && (
                  <div
                    className="absolute top-0 h-full w-0.5 bg-amber-400 opacity-70"
                    style={{ left: `${Math.min(100, (reorder / maxDisplay) * 100)}%` }}
                    title={`Reorder: ${reorder}`}
                  />
                )}
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                <span>0</span>
                <span className="text-rose-500">Min: {minimum}</span>
                <span className="text-amber-500">Reorder: {reorder}</span>
              </div>
            </div>

            {/* Thresholds */}
            <div className="space-y-2 pt-3 border-t border-slate-100">
              {[
                { label: 'Current Stock', value: `${current} ${item.unit}`, color: current <= minimum ? 'text-rose-600' : 'text-slate-800' },
                { label: 'Minimum Stock', value: `${minimum} ${item.unit}`, color: 'text-slate-600' },
                { label: 'Reorder Level', value: `${reorder} ${item.unit}`, color: 'text-slate-600' },
              ].map(r => (
                <div key={r.label} className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">{r.label}</span>
                  <span className={`font-bold ${r.color}`}>{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Item Details Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-wider mb-4">Item Details</h3>
            <div className="space-y-3">
              {[
                { icon: <Tag className="w-3.5 h-3.5 text-slate-400" />, label: 'Status', value: (item.status || '—').toUpperCase() },
                { icon: <MapPin className="w-3.5 h-3.5 text-slate-400" />, label: 'Location', value: meta.storage_location || '—' },
                { icon: <Truck className="w-3.5 h-3.5 text-slate-400" />, label: 'Supplier', value: meta.supplier || '—' },
                { icon: <BarChart3 className="w-3.5 h-3.5 text-slate-400" />, label: 'Category', value: meta.category || '—' },
                { icon: <Clock className="w-3.5 h-3.5 text-slate-400" />, label: 'Registered', value: item.created_at ? new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—' },
              ].map(r => (
                <div key={r.label} className="flex items-center justify-between text-xs gap-2">
                  <div className="flex items-center gap-1.5 text-slate-500 font-medium min-w-0">
                    {r.icon}
                    {r.label}
                  </div>
                  <span className="font-semibold text-slate-700 text-right truncate max-w-[140px]">{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Wash / Sterilization Card */}
          {isReusable && (
            <div className={`rounded-2xl border-2 shadow-sm p-5 ${washStatus === 'needs_washing' ? 'bg-rose-50 border-rose-300' : washStatus === 'clean' ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-200'}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-black text-slate-600 uppercase tracking-wider flex items-center gap-2">
                  <Droplets className="w-4 h-4" />
                  Wash Status
                </h3>
                {!isViewer && (
                  <button onClick={() => { setNewWashStatus(washStatus); setShowWashModal(true); }}
                    className="text-[10px] font-bold text-blue-600 hover:underline cursor-pointer">
                    Update
                  </button>
                )}
              </div>

              <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border ${wsCfg.bg} ${wsCfg.border}`}>
                <span className={`w-3 h-3 rounded-full flex-shrink-0 ${wsCfg.dot} ${washStatus === 'in_wash' ? 'animate-pulse' : ''}`} />
                <span className={`text-sm font-black ${wsCfg.color}`}>{wsCfg.label}</span>
              </div>

              <div className="mt-3 space-y-2">
                {washMethod && (
                  <div className="text-xs flex justify-between">
                    <span className="text-slate-500">Method</span>
                    <span className="font-semibold text-slate-700">{WASH_METHODS[washMethod] || washMethod}</span>
                  </div>
                )}
                {lastWashedAt && (
                  <div className="text-xs flex justify-between">
                    <span className="text-slate-500">Last washed</span>
                    <span className="font-semibold text-slate-700">
                      {new Date(lastWashedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                  </div>
                )}
                {lastWashedBy && (
                  <div className="text-xs flex justify-between">
                    <span className="text-slate-500">Washed by</span>
                    <span className="font-semibold text-slate-700">{lastWashedBy}</span>
                  </div>
                )}
                {meta.wash_note && (
                  <div className="text-xs text-slate-500 italic mt-1 pt-2 border-t border-slate-200">
                    "{meta.wash_note}"
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Right: Actions + Transaction Timeline ─────── */}
        <div className="lg:col-span-2 space-y-4">

          {/* Inline action panels */}
          {activeAction === 'receive' && (
            <div className="bg-white rounded-2xl border-2 border-emerald-200 shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-black text-slate-800 flex items-center gap-2">
                  <PackagePlus className="w-5 h-5 text-emerald-600" />
                  Receive Stock
                </h3>
                <button onClick={() => setActiveAction(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Quantity ({item.unit}) *</label>
                  <input type="number" step="0.1" min="0" required value={receiveQty} onChange={e => setReceiveQty(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-emerald-500" placeholder="e.g. 50" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Lot Number</label>
                  <input type="text" value={receiveLot} onChange={e => setReceiveLot(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-emerald-500" placeholder="e.g. LOT-2024-001" />
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => setActiveAction(null)} className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">Cancel</button>
                <button onClick={handleReceive} disabled={!receiveQty || receiveInv.isPending}
                  className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                  {receiveInv.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Confirm Receipt
                </button>
              </div>
            </div>
          )}

          {activeAction === 'issue' && (
            <div className="bg-white rounded-2xl border-2 border-amber-200 shadow-sm p-5">
              {washStatus === 'needs_washing' && (
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 mb-4 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                  <p className="text-xs font-bold text-rose-700">⛔ Warning: This item is marked as needing washing. Are you sure you want to issue it?</p>
                </div>
              )}
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-black text-slate-800 flex items-center gap-2">
                  <PackageMinus className="w-5 h-5 text-amber-600" />
                  Issue / Consume Stock
                </h3>
                <button onClick={() => setActiveAction(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Quantity ({item.unit}) *</label>
                  <input type="number" step="0.1" min="0" max={current} required value={issueQty} onChange={e => setIssueQty(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" placeholder={`Max: ${current}`} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Reason / Experiment</label>
                  <input type="text" value={issueReason} onChange={e => setIssueReason(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-amber-500" placeholder="e.g. CRISPR Experiment #4" />
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => setActiveAction(null)} className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">Cancel</button>
                <button onClick={handleIssue} disabled={!issueQty || issueInv.isPending}
                  className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                  {issueInv.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Confirm Issue
                </button>
              </div>
            </div>
          )}

          {/* Transaction History Timeline */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-black text-slate-700 text-sm flex items-center gap-2">
                <History className="w-4 h-4 text-blue-500" />
                Stock Movement Log
              </h3>
              <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                {transactions.length} event{transactions.length !== 1 ? 's' : ''}
              </span>
            </div>

            <div className="divide-y divide-slate-50 max-h-[420px] overflow-y-auto">
              {transactions.length === 0 ? (
                <div className="flex flex-col items-center gap-3 py-12 text-slate-400">
                  <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center">
                    <History className="w-5 h-5" />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-semibold text-slate-600">No stock movements recorded yet</p>
                    <p className="text-[10px] mt-0.5">Receive or issue stock to see the movement log.</p>
                  </div>
                </div>
              ) : (
                transactions.map((tx: any) => {
                  const cfg = getTxColor(tx.transaction_type);
                  return (
                    <div key={tx.id} className={`flex items-center justify-between px-5 py-3.5 hover:bg-slate-50/80 transition-colors`}>
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${cfg.bg} border ${cfg.border}`}>
                          {cfg.icon}
                        </div>
                        <div>
                          <span className={`text-xs font-black uppercase ${cfg.text}`}>
                            {tx.transaction_type}
                          </span>
                          {tx.remarks && (
                            <p className="text-[10px] text-slate-400 mt-0.5 max-w-[220px] truncate">{tx.remarks}</p>
                          )}
                          {tx.lot_number && (
                            <p className="text-[10px] text-slate-400 font-mono">Lot: {tx.lot_number}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-black ${cfg.text}`}>
                          {cfg.sign}{tx.quantity} <span className="text-xs font-semibold text-slate-400">{item.unit}</span>
                        </p>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          {tx.performed_at ? new Date(tx.performed_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Batches / Lot Info */}
          {batches.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <h3 className="font-black text-slate-700 text-sm flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-violet-500" />
                  Active Batches / Lots
                </h3>
              </div>
              <div className="divide-y divide-slate-50">
                {batches.map((b: any) => (
                  <div key={b.id} className="px-5 py-3 flex items-center justify-between text-xs hover:bg-slate-50">
                    <div>
                      <p className="font-bold text-slate-800 font-mono">{b.lot_number}</p>
                      {b.expiry_date && (
                        <p className={`text-[10px] mt-0.5 ${new Date(b.expiry_date) < new Date() ? 'text-rose-500 font-bold' : 'text-slate-400'}`}>
                          {new Date(b.expiry_date) < new Date() ? '⚠ EXPIRED: ' : 'Expires: '}
                          {new Date(b.expiry_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="font-black text-slate-800">{b.batch_quantity} {item.unit}</p>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${b.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                        {(b.status || 'active').toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Wash Status Update Modal ──────────────────────── */}
      {showWashModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-md shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-5 flex items-center justify-between">
              <div>
                <h3 className="text-base font-black text-white">Update Wash Status</h3>
                <p className="text-blue-100 text-xs mt-0.5 truncate max-w-[280px]">{item.item_name}</p>
              </div>
              <button onClick={() => setShowWashModal(false)} className="text-white/70 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">New Wash Status</label>
                <div className="grid grid-cols-2 gap-2">
                  {(Object.keys(WASH_STATUS_CONFIG) as WashStatus[]).map(ws => {
                    const cfg = WASH_STATUS_CONFIG[ws];
                    return (
                      <button key={ws} type="button" onClick={() => setNewWashStatus(ws)}
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold border-2 transition-all cursor-pointer ${newWashStatus === ws ? `${cfg.bg} ${cfg.color} border-current shadow-sm` : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                          }`}>
                        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                        {cfg.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {newWashStatus === 'clean' && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-emerald-700 font-medium">
                    Marking as <strong>Clean & Ready</strong> will record today's date and your name as the washer.
                  </p>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Note (Optional)</label>
                <textarea value={washNote} onChange={e => setWashNote(e.target.value)} rows={2}
                  placeholder="e.g. Autoclaved at 121°C for 20 min, triple DI water rinse…"
                  className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>

              <div className="flex justify-end gap-3 pt-1">
                <button onClick={() => setShowWashModal(false)} className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">Cancel</button>
                <button onClick={handleUpdateWashStatus} disabled={updateItem.isPending}
                  className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                  {updateItem.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Save Wash Status
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
