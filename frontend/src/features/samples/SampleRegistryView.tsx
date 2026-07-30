import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { Search, Plus, ArrowUpRight, MapPin, Loader2, AlertCircle } from 'lucide-react';
import { useSamples, useCreateSample } from '../../hooks/useSamples';
import { useExperiments } from '../../hooks/useExperiments';
import { useAuth } from '../../providers/AuthProvider';

interface SampleRegistryViewProps {
  onSelectSample: (sampleId: string) => void;
  onSelectView: (view: ViewMode) => void;
}

export const SampleRegistryView: React.FC<SampleRegistryViewProps> = ({
  onSelectSample,
  onSelectView
}) => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>(''); // '' means All
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: samplesData, isLoading, error } = useSamples(
    page, 
    pageSize, 
    undefined, 
    selectedStatus ? selectedStatus.toLowerCase() : undefined,
    searchQuery
  );
  
  const createSample = useCreateSample();

  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [typeCode, setTypeCode] = useState<string>('CELL_LINE');
  const [qty, setQty] = useState('');
  const [sampleCode, setSampleCode] = useState(`SMP-${Math.floor(1000 + Math.random() * 9000)}`);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string>('');

  const { data: experimentsData } = useExperiments(1, 100);
  
  const statuses = [{ label: 'All', value: '' }, { label: 'Available', value: 'available' }, { label: 'Consumed', value: 'consumed' }, { label: 'Expired', value: 'expired' }];

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
        unit: 'vials',
        storage_temperature: '-80C',
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        experiment_id: selectedExperimentId,
        metadata_json: { typeCode, locationString: 'Freezer -20°C (Unit #2) - Rack A, Box 01' }
      });
      
      setName('');
      setQty('');
      setSampleCode(`SMP-${Math.floor(1000 + Math.random() * 9000)}`);
      setShowModal(false);
    } catch (err) {
      console.error("Failed to create sample:", err);
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
              placeholder="Search sample by ID, barcode, or name..."
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs font-semibold text-slate-400 mr-1">Status:</span>
          {statuses.map((st) => (
            <button
              key={st.value}
              onClick={() => setSelectedStatus(st.value)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                selectedStatus === st.value
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st.label}
            </button>
          ))}

          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors ml-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Register Sample</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12 h-full items-center">
           <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-12 h-full text-rose-500">
           <AlertCircle className="w-8 h-8 mb-4" />
           <span className="font-semibold">Failed to load samples.</span>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Sample Code</th>
                    <th className="py-3 px-4">Barcode</th>
                    <th className="py-3 px-4">Sample Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Storage Location</th>
                    <th className="py-3 px-4">Quantity</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {samplesData?.items.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{s.sample_code}</td>
                      <td className="py-3 px-4 text-slate-600 font-mono">{s.barcode}</td>
                      <td className="py-3 px-4 text-slate-800 font-semibold">{s.sample_name}</td>
                      <td className="py-3 px-4">
                        <span className="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded text-[10px]">
                          {s.metadata_json?.typeCode || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                        <span className="truncate max-w-[180px]">{s.metadata_json?.locationString || 'Unassigned'}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{s.quantity} {s.unit}</td>
                      <td className="py-3 px-4">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          s.status === 'available' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {s.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => onSelectSample(s.id)}
                          className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1 justify-end ml-auto cursor-pointer"
                        >
                          <span>Inventory Detail</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {samplesData?.items.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        No samples found matching your criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {samplesData && samplesData.total_pages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-6">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 rounded-lg disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-xs text-slate-600 font-semibold">Page {page} of {samplesData.total_pages}</span>
              <button 
                disabled={page >= samplesData.total_pages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 rounded-lg disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">Register Biological / Chemical Sample</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Sample Code</label>
                <input
                  type="text"
                  required
                  value={sampleCode}
                  onChange={(e) => setSampleCode(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500 font-mono text-slate-500 bg-slate-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Sample Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. HEK293T Cell Line - Passage 14"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Type</label>
                <select
                  value={typeCode}
                  onChange={(e) => setTypeCode(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                >
                  <option value="CELL_LINE">Cell Line</option>
                  <option value="PLASMID">Plasmid</option>
                  <option value="REAGENT">Reagent</option>
                  <option value="PROTEIN">Protein</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Experiment</label>
                <select
                  required
                  value={selectedExperimentId}
                  onChange={(e) => setSelectedExperimentId(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                >
                  <option value="" disabled>Select an Experiment</option>
                  {experimentsData?.items.map(exp => (
                    <option key={exp.id} value={exp.id}>{exp.title}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity (Number)</label>
                <input
                  type="number"
                  step="0.1"
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                  placeholder="e.g. 5"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSample.isPending}
                  className="px-4 py-2 text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-lg shadow-sm cursor-pointer disabled:opacity-50"
                >
                  {createSample.isPending ? 'Registering...' : 'Save Sample'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
