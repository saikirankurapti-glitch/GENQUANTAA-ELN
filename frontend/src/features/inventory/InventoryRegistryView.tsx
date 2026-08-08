import React, { useState, useMemo } from 'react';
import type { ViewMode } from '../../types';
import {
  Search, Plus, ArrowUpRight, Loader2, AlertCircle,
  AlertTriangle, Package, TrendingDown, CheckCircle2,
  X, Check, ChevronRight, Filter, ShieldCheck,
  Droplets, FlaskConical, Thermometer, BarChart3,
  RefreshCw, Clock, Trash2, Beaker, Wind
} from 'lucide-react';
import { useInventory, useCreateInventoryItem, useReceiveInventory } from '../../hooks/useInventory';
import { useAuth } from '../../providers/AuthProvider';
import { isStrictlyViewer } from '../../utils/permissions';

interface InventoryRegistryViewProps {
  onSelectInventoryItem: (id: string) => void;
  onSelectView: (view: ViewMode) => void;
}

const CATEGORIES = [
  { code: '', label: 'All Categories', icon: '📦' },
  { code: 'REAGENTS', label: 'Reagents', icon: '⚗️' },
  { code: 'CONSUMABLES', label: 'Consumables', icon: '🧤' },
  { code: 'CHEMICALS', label: 'Chemicals', icon: '🧪' },
  { code: 'GLASSWARE', label: 'Glassware', icon: '🫙' },
  { code: 'PPE', label: 'PPE', icon: '🥽' },
  { code: 'MEDIA', label: 'Cell Media', icon: '🧫' },
];

// Wash method options
const WASH_METHODS = [
  { code: 'autoclave', label: 'Autoclave (121°C)', icon: '♨️' },
  { code: 'manual_hot', label: 'Manual Hot Wash', icon: '🫧' },
  { code: 'detergent_rinse', label: 'Detergent + DI Rinse', icon: '💧' },
  { code: 'acid_wash', label: 'Acid Wash', icon: '⚗️' },
  { code: 'ethanol_wipe', label: '70% EtOH Wipe', icon: '🧴' },
  { code: 'uv_sterilize', label: 'UV Sterilization', icon: '🔆' },
  { code: 'dishwasher', label: 'Lab Dishwasher', icon: '🫙' },
  { code: 'disposable', label: 'Disposable (N/A)', icon: '🗑️' },
];

type WashStatus = 'clean' | 'needs_washing' | 'in_wash' | 'not_applicable';

const WASH_STATUS_CONFIG: Record<WashStatus, { label: string; color: string; bg: string; border: string; dot: string }> = {
  clean:          { label: 'Clean & Ready',    color: 'text-emerald-700', bg: 'bg-emerald-50',  border: 'border-emerald-200', dot: 'bg-emerald-400' },
  needs_washing:  { label: 'Needs Washing',    color: 'text-rose-700',    bg: 'bg-rose-50',     border: 'border-rose-200',    dot: 'bg-rose-500' },
  in_wash:        { label: 'In Wash Cycle',    color: 'text-amber-700',   bg: 'bg-amber-50',    border: 'border-amber-200',   dot: 'bg-amber-400' },
  not_applicable: { label: 'Disposable / N/A', color: 'text-slate-600',   bg: 'bg-slate-50',    border: 'border-slate-200',   dot: 'bg-slate-300' },
};

// Derive wash status from metadata (frontend-only feature layered over metadata_json)
const getWashStatus = (item: any): WashStatus => {
  return item.metadata_json?.wash_status || 'not_applicable';
};

const getStockPercent = (current: number, min: number, reorder: number) => {
  const max = Math.max(reorder * 2, current * 1.2, 10);
  return Math.min(100, Math.round((current / max) * 100));
};

const getStockColor = (isLow: boolean, current: number, min: number) => {
  if (current <= min) return 'bg-rose-500';
  if (isLow) return 'bg-amber-500';
  return 'bg-emerald-500';
};

export const InventoryRegistryView: React.FC<InventoryRegistryViewProps> = ({
  onSelectInventoryItem,
}) => {
  const { user } = useAuth();
  const isViewer = isStrictlyViewer(user);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [washFilter, setWashFilter] = useState<WashStatus | ''>('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Receive Stock modal
  const [receiveModal, setReceiveModal] = useState<{ id: string; name: string; unit: string } | null>(null);
  const [receiveQty, setReceiveQty] = useState('');
  const [receiveLot, setReceiveLot] = useState('');
  const [receiveSupplier, setReceiveSupplier] = useState('');

  // New Item modal
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState(1);
  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState(`INV-${Math.floor(1000 + Math.random() * 9000)}`);
  const [newCategory, setNewCategory] = useState('REAGENTS');
  const [newUnit, setNewUnit] = useState('units');
  const [newInitialStock, setNewInitialStock] = useState('');
  const [newMinStock, setNewMinStock] = useState('5');
  const [newReorderLevel, setNewReorderLevel] = useState('10');
  const [newSupplier, setNewSupplier] = useState('');
  const [newStorageLocation, setNewStorageLocation] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [newWashMethod, setNewWashMethod] = useState('disposable');
  const [newWashStatus, setNewWashStatus] = useState<WashStatus>('not_applicable');
  const [newIsReusable, setNewIsReusable] = useState(false);

  const { data: inventoryData, isLoading, error } = useInventory(
    page, pageSize, undefined, undefined, undefined,
    undefined,
    showLowStockOnly ? true : undefined,
    searchQuery
  );

  const createItem = useCreateInventoryItem();
  const receiveInventory = useReceiveInventory();

  // KPIs
  const totalItems = inventoryData?.total ?? 0;
  const lowStockItems = inventoryData?.items.filter(i => i.is_low_stock).length ?? 0;
  const washNeeded = inventoryData?.items.filter(i => getWashStatus(i) === 'needs_washing').length ?? 0;
  const cleanReady = inventoryData?.items.filter(i => getWashStatus(i) === 'clean').length ?? 0;

  // Filter by wash status and category locally
  const displayItems = useMemo(() => {
    if (!inventoryData?.items) return [];
    let items = inventoryData.items;
    if (selectedCategory) items = items.filter(i => i.metadata_json?.category === selectedCategory);
    if (washFilter) items = items.filter(i => getWashStatus(i) === washFilter);
    return items;
  }, [inventoryData, selectedCategory, washFilter]);

  const handleReceiveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiveModal || !receiveQty) return;
    try {
      await receiveInventory.mutateAsync({
        id: receiveModal.id,
        data: { quantity: parseFloat(receiveQty), lot_number: receiveLot, notes: receiveSupplier }
      });
      setReceiveModal(null); setReceiveQty(''); setReceiveLot(''); setReceiveSupplier('');
    } catch (err) { console.error(err); }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await createItem.mutateAsync({
        item_code: newCode,
        item_name: newName,
        unit: newUnit,
        minimum_stock: parseFloat(newMinStock) || 5,
        reorder_level: parseFloat(newReorderLevel) || 10,
        status: 'available',
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        initial_stock: parseFloat(newInitialStock) || 0,
        metadata_json: {
          category: newCategory,
          supplier: newSupplier,
          storage_location: newStorageLocation,
          notes: newNotes,
          wash_method: newWashMethod,
          wash_status: newWashStatus,
          is_reusable: newIsReusable,
          last_washed_at: newWashStatus === 'clean' ? new Date().toISOString() : null,
          last_washed_by: newWashStatus === 'clean' ? (user?.first_name || user?.username || 'Unknown') : null,
        }
      });
      resetModal();
    } catch (err) { console.error(err); }
  };

  const resetModal = () => {
    setShowModal(false); setStep(1); setNewName('');
    setNewCode(`INV-${Math.floor(1000 + Math.random() * 9000)}`);
    setNewCategory('REAGENTS'); setNewUnit('units');
    setNewInitialStock(''); setNewMinStock('5'); setNewReorderLevel('10');
    setNewSupplier(''); setNewStorageLocation(''); setNewNotes('');
    setNewWashMethod('disposable'); setNewWashStatus('not_applicable'); setNewIsReusable(false);
  };

  const getCatInfo = (code: string) => CATEGORIES.find(c => c.code === code) || CATEGORIES[0];

  return (
    <div className="p-5 space-y-5 bg-slate-50 min-h-full">

      {/* ── KPI Bar ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Stock Items',
            value: totalItems,
            sub: `Showing page ${page}`,
            gradient: 'from-indigo-600 to-blue-600',
            icon: <Package className="w-5 h-5" />,
          },
          {
            label: 'Low Stock Alerts',
            value: lowStockItems,
            sub: lowStockItems > 0 ? 'Reorder required' : 'All stocked',
            gradient: lowStockItems > 0 ? 'from-rose-500 to-rose-700' : 'from-slate-400 to-slate-600',
            icon: <TrendingDown className="w-5 h-5" />,
          },
          {
            label: 'Needs Washing',
            value: washNeeded,
            sub: washNeeded > 0 ? 'Must wash before use' : 'All clean',
            gradient: washNeeded > 0 ? 'from-amber-500 to-orange-600' : 'from-slate-400 to-slate-600',
            icon: <Droplets className="w-5 h-5" />,
          },
          {
            label: 'Clean & Ready',
            value: cleanReady,
            sub: 'Verified clean items',
            gradient: 'from-emerald-500 to-teal-600',
            icon: <CheckCircle2 className="w-5 h-5" />,
          },
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

      {/* ── Critical Low Stock Banner ────────────────────── */}
      {lowStockItems > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-start gap-3">
          <div className="w-9 h-9 bg-rose-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-rose-800">
              {lowStockItems} item{lowStockItems > 1 ? 's' : ''} below reorder threshold
            </p>
            <p className="text-xs text-rose-600 mt-0.5">
              {inventoryData?.items.filter(i => i.is_low_stock).map(i => i.item_name).join(' · ')}
            </p>
          </div>
          <button
            onClick={() => setShowLowStockOnly(!showLowStockOnly)}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
              showLowStockOnly ? 'bg-rose-600 text-white border-rose-600' : 'bg-white text-rose-600 border-rose-300 hover:bg-rose-50'
            }`}
          >
            {showLowStockOnly ? 'Show All' : 'Filter Low Stock'}
          </button>
        </div>
      )}

      {/* ── Wash Warning Banner ─────────────────────────── */}
      {washNeeded > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
          <div className="w-9 h-9 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <Droplets className="w-5 h-5 text-amber-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-amber-800">
              ⚠️ {washNeeded} item{washNeeded > 1 ? 's' : ''} require washing before use
            </p>
            <p className="text-xs text-amber-700 mt-0.5">
              Do not use these items until they have been properly washed and verified clean.
            </p>
          </div>
          <button
            onClick={() => setWashFilter(washFilter === 'needs_washing' ? '' : 'needs_washing')}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
              washFilter === 'needs_washing' ? 'bg-amber-600 text-white border-amber-600' : 'bg-white text-amber-600 border-amber-300 hover:bg-amber-50'
            }`}
          >
            {washFilter === 'needs_washing' ? 'Show All' : 'Show Dirty Items'}
          </button>
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
              placeholder="Search inventory by code, name, or supplier…"
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
            />
          </div>
          {!isViewer && (
            <button
              onClick={() => { setShowModal(true); setStep(1); }}
              className="flex items-center gap-2 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-700 hover:to-pink-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              Add Stock Item
            </button>
          )}
        </div>

        {/* Category chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Category</span>
          {CATEGORIES.map(c => (
            <button
              key={c.code}
              onClick={() => setSelectedCategory(c.code)}
              className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                selectedCategory === c.code
                  ? 'bg-rose-600 text-white border-rose-600 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-rose-50 hover:border-rose-300'
              }`}
            >
              <span>{c.icon}</span>
              {c.label}
            </button>
          ))}
        </div>

        {/* Wash status filter chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Wash Status</span>
          <button
            onClick={() => setWashFilter('')}
            className={`text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
              washFilter === '' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            All
          </button>
          {(Object.keys(WASH_STATUS_CONFIG) as WashStatus[]).map(ws => {
            const cfg = WASH_STATUS_CONFIG[ws];
            return (
              <button
                key={ws}
                onClick={() => setWashFilter(washFilter === ws ? '' : ws)}
                className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                  washFilter === ws
                    ? `${cfg.bg} ${cfg.color} ${cfg.border}`
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                {cfg.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Table ───────────────────────────────────────── */}
      {isLoading ? (
        <div className="flex flex-col justify-center p-16 items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-rose-600" />
          <span className="text-xs text-slate-400 font-medium">Loading inventory…</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-16 text-rose-500 gap-3">
          <AlertCircle className="w-8 h-8" />
          <span className="font-semibold text-sm">Failed to load inventory.</span>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-600">
                {displayItems.length} item{displayItems.length !== 1 ? 's' : ''}
                {selectedCategory && ` · ${getCatInfo(selectedCategory).label}`}
                {washFilter && ` · ${WASH_STATUS_CONFIG[washFilter]?.label}`}
              </span>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Filter className="w-3.5 h-3.5" />
                Active filters: {[selectedCategory, washFilter, searchQuery, showLowStockOnly ? '1' : ''].filter(Boolean).length}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                  <tr>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Item Code</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Name / Category</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Stock Level</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Wash Status</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Last Washed</th>
                    <th className="py-3 px-4 font-bold uppercase tracking-wide text-[10px]">Stock Status</th>
                    <th className="py-3 px-4 text-right font-bold uppercase tracking-wide text-[10px]">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 font-medium">
                  {displayItems.map((inv) => {
                    const ws = getWashStatus(inv);
                    const wsCfg = WASH_STATUS_CONFIG[ws] || WASH_STATUS_CONFIG.not_applicable;
                    const cat = getCatInfo(inv.metadata_json?.category || '');
                    const stockPct = getStockPercent(inv.current_stock, inv.minimum_stock, inv.reorder_level);
                    const stockBarColor = getStockColor(inv.is_low_stock, inv.current_stock, inv.minimum_stock);
                    const lastWashedAt = inv.metadata_json?.last_washed_at;
                    const lastWashedBy = inv.metadata_json?.last_washed_by;
                    const isReusable = inv.metadata_json?.is_reusable;

                    return (
                      <tr key={inv.id} className="hover:bg-slate-50/80 transition-colors group">
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${wsCfg.dot}`} />
                            <span className="font-mono font-bold text-rose-600">{inv.item_code}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div>
                            <span className="font-semibold text-slate-800">{inv.item_name}</span>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[10px] text-slate-500">{cat.icon} {cat.label || 'Uncategorized'}</span>
                              {isReusable && (
                                <span className="text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-200 px-1.5 py-0.5 rounded">
                                  ♻ Reusable
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 min-w-[140px]">
                          <div className="space-y-1.5">
                            <div className="flex justify-between text-[10px]">
                              <span className={`font-bold ${inv.is_low_stock ? 'text-rose-600' : 'text-slate-700'}`}>
                                {inv.current_stock} {inv.unit}
                              </span>
                              <span className="text-slate-400">Min: {inv.minimum_stock}</span>
                            </div>
                            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${stockBarColor}`}
                                style={{ width: `${stockPct}%` }}
                              />
                            </div>
                            <div className="text-[10px] text-slate-400">Reorder @ {inv.reorder_level}</div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-bold ${wsCfg.bg} ${wsCfg.color} ${wsCfg.border}`}>
                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${wsCfg.dot} ${ws === 'in_wash' ? 'animate-pulse' : ''}`} />
                            {wsCfg.label}
                          </div>
                          {ws === 'needs_washing' && (
                            <p className="text-[10px] text-rose-500 font-semibold mt-1">⛔ Do not use</p>
                          )}
                          {ws === 'in_wash' && (
                            <p className="text-[10px] text-amber-600 font-semibold mt-1">🔄 Processing…</p>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {lastWashedAt ? (
                            <div>
                              <p className="text-[10px] font-semibold text-slate-700">
                                {new Date(lastWashedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                              </p>
                              {lastWashedBy && (
                                <p className="text-[10px] text-slate-400 mt-0.5">by {lastWashedBy}</p>
                              )}
                            </div>
                          ) : (
                            <span className="text-[10px] text-slate-400 italic">Not recorded</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${
                            inv.is_low_stock
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}>
                            {inv.is_low_stock ? '⚠ LOW STOCK' : '✓ AVAILABLE'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-1.5 justify-end">
                            {!isViewer && (
                              <button
                                onClick={() => setReceiveModal({ id: inv.id, name: inv.item_name, unit: inv.unit })}
                                className="flex items-center gap-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-[10px] font-bold px-2 py-1.5 rounded-lg border border-emerald-200 transition-all cursor-pointer"
                                title="Receive Stock"
                              >
                                <RefreshCw className="w-3 h-3" />
                                Receive
                              </button>
                            )}
                            <button
                              onClick={() => onSelectInventoryItem(inv.id)}
                              className="flex items-center gap-1 bg-rose-50 hover:bg-rose-100 text-rose-700 text-[10px] font-bold px-2 py-1.5 rounded-lg border border-rose-200 transition-all cursor-pointer"
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
                            <Package className="w-6 h-6" />
                          </div>
                          <div>
                            <p className="font-semibold text-slate-600">No inventory items found</p>
                            <p className="text-xs mt-1">Try adjusting your filters or add a new stock item.</p>
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
          {inventoryData && inventoryData.total_pages > 1 && (
            <div className="flex justify-center items-center gap-3">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl disabled:opacity-40 hover:bg-slate-50 cursor-pointer shadow-sm">
                ← Previous
              </button>
              <span className="text-xs text-slate-500 font-bold bg-white border border-slate-200 px-4 py-2 rounded-xl shadow-sm">
                Page {page} of {inventoryData.total_pages}
              </span>
              <button disabled={page >= inventoryData.total_pages} onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl disabled:opacity-40 hover:bg-slate-50 cursor-pointer shadow-sm">
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* ── Receive Stock Quick Modal ────────────────────── */}
      {receiveModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-md shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-5 flex items-center justify-between">
              <div>
                <h3 className="text-base font-black text-white">Receive Stock</h3>
                <p className="text-emerald-100 text-xs mt-0.5 truncate max-w-[280px]">{receiveModal.name}</p>
              </div>
              <button onClick={() => setReceiveModal(null)} className="text-white/70 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleReceiveSubmit} className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Quantity ({receiveModal.unit}) <span className="text-rose-500">*</span></label>
                  <input type="number" step="0.1" min="0" required value={receiveQty} onChange={e => setReceiveQty(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-emerald-500" placeholder="e.g. 50" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Lot Number</label>
                  <input type="text" value={receiveLot} onChange={e => setReceiveLot(e.target.value)}
                    className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-emerald-500" placeholder="e.g. LOT-2024-001" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Supplier / Notes</label>
                <input type="text" value={receiveSupplier} onChange={e => setReceiveSupplier(e.target.value)}
                  className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-emerald-500" placeholder="Supplier name or delivery notes" />
              </div>
              <div className="flex justify-end gap-3 pt-1">
                <button type="button" onClick={() => setReceiveModal(null)} className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer">Cancel</button>
                <button type="submit" disabled={receiveInventory.isPending}
                  className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                  {receiveInventory.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  Confirm Receipt
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── New Item Multi-Step Modal ────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            <div className="bg-gradient-to-r from-rose-600 to-pink-600 p-5 flex items-center justify-between flex-shrink-0">
              <div>
                <h3 className="text-base font-black text-white">New Stock Item</h3>
                <p className="text-rose-100 text-xs mt-0.5">
                  Step {step} of 3 — {step === 1 ? 'Item Identity' : step === 2 ? 'Stock & Storage + Wash Setup' : 'Review & Confirm'}
                </p>
              </div>
              <button onClick={resetModal} className="text-white/70 hover:text-white cursor-pointer"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex flex-shrink-0">
              {[1, 2, 3].map(s => (
                <div key={s} className={`flex-1 h-1 ${s <= step ? 'bg-rose-500' : 'bg-slate-100'}`} />
              ))}
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 overflow-y-auto">
              {/* Step 1 */}
              {step === 1 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Item Code</label>
                      <input type="text" required value={newCode} onChange={e => setNewCode(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500 font-mono" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Item Name <span className="text-rose-500">*</span></label>
                      <input type="text" required value={newName} onChange={e => setNewName(e.target.value)}
                        placeholder="e.g. DMEM Cell Culture Media" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">Category</label>
                    <div className="grid grid-cols-3 gap-2">
                      {CATEGORIES.filter(c => c.code).map(c => (
                        <button key={c.code} type="button" onClick={() => setNewCategory(c.code)}
                          className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold border-2 transition-all cursor-pointer ${
                            newCategory === c.code ? 'bg-rose-50 text-rose-700 border-rose-400' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                          }`}>
                          <span>{c.icon}</span>{c.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Unit</label>
                      <select value={newUnit} onChange={e => setNewUnit(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500 bg-white">
                        {['units', 'mL', 'L', 'mg', 'g', 'kg', 'vials', 'boxes', 'packs', 'pairs'].map(u => (
                          <option key={u} value={u}>{u}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Supplier</label>
                      <input type="text" value={newSupplier} onChange={e => setNewSupplier(e.target.value)}
                        placeholder="e.g. Sigma-Aldrich" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
                    </div>
                  </div>

                  {/* Reusable toggle */}
                  <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded-xl">
                    <input
                      type="checkbox"
                      id="isReusable"
                      checked={newIsReusable}
                      onChange={e => {
                        setNewIsReusable(e.target.checked);
                        if (e.target.checked) {
                          setNewWashStatus('needs_washing');
                          setNewWashMethod('manual_hot');
                        } else {
                          setNewWashStatus('not_applicable');
                          setNewWashMethod('disposable');
                        }
                      }}
                      className="w-4 h-4 accent-blue-600 cursor-pointer"
                    />
                    <label htmlFor="isReusable" className="text-xs font-semibold text-blue-700 cursor-pointer flex items-center gap-2">
                      <RefreshCw className="w-4 h-4" />
                      This is a reusable item (glassware, equipment, containers)
                    </label>
                  </div>
                </div>
              )}

              {/* Step 2 — Stock + Wash */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Initial Stock</label>
                      <input type="number" min="0" value={newInitialStock} onChange={e => setNewInitialStock(e.target.value)}
                        placeholder="0" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Min Stock</label>
                      <input type="number" min="0" value={newMinStock} onChange={e => setNewMinStock(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1.5">Reorder Level</label>
                      <input type="number" min="0" value={newReorderLevel} onChange={e => setNewReorderLevel(e.target.value)}
                        className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">Storage Location</label>
                    <input type="text" value={newStorageLocation} onChange={e => setNewStorageLocation(e.target.value)}
                      placeholder="e.g. Reagent Cabinet B, Shelf 2" className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
                  </div>

                  {/* Wash / Cleaning Section */}
                  <div className="border-t border-slate-200 pt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Droplets className="w-4 h-4 text-blue-600" />
                      </div>
                      <h4 className="text-xs font-black text-slate-700">Wash & Sterilization Protocol</h4>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-2">Current Wash Status</label>
                      <div className="grid grid-cols-2 gap-2">
                        {(Object.keys(WASH_STATUS_CONFIG) as WashStatus[]).map(ws => {
                          const cfg = WASH_STATUS_CONFIG[ws];
                          return (
                            <button key={ws} type="button" onClick={() => setNewWashStatus(ws)}
                              className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold border-2 transition-all cursor-pointer ${
                                newWashStatus === ws ? `${cfg.bg} ${cfg.color} border-current` : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                              }`}>
                              <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                              {cfg.label}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {newWashStatus !== 'not_applicable' && (
                      <div className="mt-3">
                        <label className="block text-xs font-bold text-slate-700 mb-2">Wash Method</label>
                        <div className="grid grid-cols-2 gap-2">
                          {WASH_METHODS.filter(m => m.code !== 'disposable').map(m => (
                            <button key={m.code} type="button" onClick={() => setNewWashMethod(m.code)}
                              className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold border-2 transition-all cursor-pointer text-left ${
                                newWashMethod === m.code ? 'bg-blue-50 text-blue-700 border-blue-400' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                              }`}>
                              <span className="text-base">{m.icon}</span>
                              {m.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">Notes</label>
                    <textarea value={newNotes} onChange={e => setNewNotes(e.target.value)} rows={2}
                      placeholder="Additional handling or storage instructions…"
                      className="w-full border border-slate-200 rounded-xl p-2.5 text-xs focus:ring-2 focus:ring-rose-500 resize-none" />
                  </div>
                </div>
              )}

              {/* Step 3 — Review */}
              {step === 3 && (
                <div className="space-y-4">
                  <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5 space-y-2.5">
                    <h4 className="text-xs font-black text-slate-700 uppercase tracking-wider mb-3">Review Item Details</h4>
                    {[
                      { label: 'Code', value: newCode },
                      { label: 'Name', value: newName },
                      { label: 'Category', value: getCatInfo(newCategory).label || newCategory },
                      { label: 'Unit', value: newUnit },
                      { label: 'Initial Stock', value: newInitialStock || '0' },
                      { label: 'Min / Reorder', value: `${newMinStock} / ${newReorderLevel}` },
                      { label: 'Storage', value: newStorageLocation || '—' },
                      { label: 'Wash Status', value: WASH_STATUS_CONFIG[newWashStatus]?.label },
                      { label: 'Wash Method', value: WASH_METHODS.find(m => m.code === newWashMethod)?.label || '—' },
                      { label: 'Reusable', value: newIsReusable ? 'Yes ♻' : 'No (Disposable)' },
                    ].map(row => (
                      <div key={row.label} className="flex items-center justify-between text-xs border-b border-slate-200 pb-2 last:border-0 last:pb-0">
                        <span className="text-slate-500 font-medium">{row.label}</span>
                        <span className="font-bold text-slate-800">{row.value}</span>
                      </div>
                    ))}
                  </div>
                  {newIsReusable && newWashStatus === 'needs_washing' && (
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-amber-700 font-medium">
                        This item will be marked <strong>Needs Washing</strong>. Scientists will see a warning not to use it until it is washed.
                      </p>
                    </div>
                  )}
                  {newWashStatus === 'clean' && (
                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-emerald-700 font-medium">
                        Item will be added as <strong>Clean & Ready to use</strong> with today's wash date recorded.
                      </p>
                    </div>
                  )}
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
                    {[1, 2, 3].map(s => (
                      <div key={s} className={`w-2 h-2 rounded-full ${s === step ? 'bg-rose-600' : 'bg-slate-200'}`} />
                    ))}
                  </div>
                  {step < 3 ? (
                    <button type="button" onClick={() => setStep(s => s + 1)}
                      disabled={step === 1 && !newName.trim()}
                      className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                      Continue <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button type="submit" disabled={createItem.isPending}
                      className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-gradient-to-r from-rose-600 to-pink-600 text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50">
                      {createItem.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      {createItem.isPending ? 'Adding…' : 'Add to Inventory'}
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
