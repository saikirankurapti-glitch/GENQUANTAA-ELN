import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { Search, Plus, ArrowUpRight, Loader2, AlertCircle } from 'lucide-react';
import { useInstruments, useCreateInstrument } from '../../hooks/useInstruments';
import { useAuth } from '../../providers/AuthProvider';

interface InstrumentRegistryViewProps {
  onSelectInstrument: (id: string) => void;
  onSelectView: (view: ViewMode) => void;
}

export const InstrumentRegistryView: React.FC<InstrumentRegistryViewProps> = ({
  onSelectInstrument,
  onSelectView
}) => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: instrumentData, isLoading, error } = useInstruments(
    page, pageSize, undefined, undefined, undefined, undefined, searchQuery
  );

  const createInstrument = useCreateInstrument();

  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [code, setCode] = useState(`INS-${Math.floor(1000 + Math.random() * 9000)}`);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      await createInstrument.mutateAsync({
        instrument_code: code,
        instrument_name: name,
        serial_number: `SN-${Math.floor(Math.random() * 90000)}`,
        asset_tag: `AT-${Math.floor(Math.random() * 90000)}`,
        manufacturer: 'Default Manufacturer',
        model: 'Model-X',
        operational_status: 'operational',
        availability_status: 'available',
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        metadata_json: {},
      });
      setName('');
      setCode(`INS-${Math.floor(1000 + Math.random() * 9000)}`);
      setShowModal(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Instruments..."
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Add Instrument</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12 h-full items-center">
           <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-12 h-full text-rose-500">
           <AlertCircle className="w-8 h-8 mb-4" />
           <span className="font-semibold">Failed to load instruments.</span>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Manufacturer</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {instrumentData?.items.map((ins) => (
                <tr key={ins.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-amber-600">{ins.instrument_code}</td>
                  <td className="py-3 px-4 text-slate-800 font-semibold">{ins.instrument_name}</td>
                  <td className="py-3 px-4 text-slate-600">{ins.manufacturer} {ins.model}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      ins.operational_status === 'operational' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                    }`}>
                      {ins.operational_status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectInstrument(ins.id)}
                      className="text-xs font-semibold text-amber-600 hover:text-amber-700 flex items-center gap-1 justify-end ml-auto cursor-pointer"
                    >
                      <span>Manage</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {instrumentData?.items.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-slate-500">No instruments found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">New Instrument</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Code</label>
                <input type="text" required value={code} onChange={(e) => setCode(e.target.value)} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-amber-500 font-mono" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Name</label>
                <input type="text" required value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-amber-500" />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer">Cancel</button>
                <button type="submit" disabled={createInstrument.isPending} className="px-4 py-2 text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white rounded-lg shadow-sm cursor-pointer disabled:opacity-50">Create Instrument</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
