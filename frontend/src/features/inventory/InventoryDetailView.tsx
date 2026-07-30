import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { ArrowLeft, Loader2, AlertCircle, PackageMinus, PackagePlus, History } from 'lucide-react';
import { useInventoryItem, useReceiveInventory, useIssueInventory } from '../../hooks/useInventory';

interface InventoryDetailViewProps {
  inventoryId: string;
  onSelectView: (view: ViewMode) => void;
}

export const InventoryDetailView: React.FC<InventoryDetailViewProps> = ({
  inventoryId,
  onSelectView
}) => {
  const { data: item, isLoading, error } = useInventoryItem(inventoryId);
  const receiveInv = useReceiveInventory();
  const issueInv = useIssueInventory();

  const [qty, setQty] = useState('');

  const handleReceive = async () => {
    if (!item || !qty) return;
    await receiveInv.mutateAsync({
      id: item.id,
      data: { quantity: parseFloat(qty), remarks: "Received from UI" }
    });
    setQty('');
  };

  const handleIssue = async () => {
    if (!item || !qty) return;
    await issueInv.mutateAsync({
      id: item.id,
      data: { quantity: parseFloat(qty), remarks: "Issued from UI" }
    });
    setQty('');
  };

  if (isLoading) return <div className="flex justify-center p-12 h-full items-center"><Loader2 className="w-8 h-8 animate-spin text-rose-600" /></div>;
  if (error || !item) return <div className="flex justify-center p-12 h-full text-rose-500"><AlertCircle className="w-8 h-8" /></div>;

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => onSelectView('inventory')} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-mono">{item.item_code}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{item.item_name}</h2>
          </div>
        </div>
        <div className="flex items-center gap-4 border-l border-slate-200 pl-4">
          <div className="flex flex-col items-end">
            <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Current Stock</span>
            <span className={`text-xl font-bold ${item.is_low_stock ? 'text-rose-600' : 'text-slate-800'}`}>
              {item.current_stock} {item.unit}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2">Stock Actions</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity</label>
              <input type="number" step="0.1" value={qty} onChange={(e) => setQty(e.target.value)} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-rose-500" />
            </div>
            <div className="flex gap-3">
              <button onClick={handleReceive} disabled={!qty || receiveInv.isPending} className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer disabled:opacity-50">
                <PackagePlus className="w-4 h-4" /> Receive
              </button>
              <button onClick={handleIssue} disabled={!qty || issueInv.isPending} className="flex-1 flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer disabled:opacity-50">
                <PackageMinus className="w-4 h-4" /> Issue / Consume
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <History className="w-4 h-4 text-blue-500" /> Transactions
          </h3>
          <div className="space-y-3 h-64 overflow-y-auto">
            {item.transactions.length === 0 ? (
              <p className="text-xs text-slate-500">No transactions recorded.</p>
            ) : (
              item.transactions.map((tx) => (
                <div key={tx.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs flex justify-between items-center">
                  <div>
                    <span className={`font-bold uppercase ${tx.transaction_type === 'receive' ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {tx.transaction_type}
                    </span>
                    <p className="text-slate-500">{new Date(tx.performed_at).toLocaleString()}</p>
                  </div>
                  <div className="font-bold text-slate-800 text-sm">
                    {tx.transaction_type === 'receive' ? '+' : '-'}{tx.quantity} {item.unit}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
