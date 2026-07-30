import React, { useState } from 'react';
import { Sample, ViewMode } from '../../types';
import { TestTube2, Search, Filter, Plus, QrCode, ArrowUpRight, MapPin, CheckCircle2, AlertTriangle } from 'lucide-react';

interface SampleRegistryViewProps {
  samples: Sample[];
  onSelectSample: (sampleId: string) => void;
  onSelectView: (view: ViewMode) => void;
  onCreateSample: (sample: Partial<Sample>) => void;
}

export const SampleRegistryView: React.FC<SampleRegistryViewProps> = ({
  samples,
  onSelectSample,
  onSelectView,
  onCreateSample
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [showModal, setShowModal] = useState(false);

  // New sample state
  const [name, setName] = useState('');
  const [type, setType] = useState<Sample['type']>('Cell Line');
  const [qty, setQty] = useState('');

  const types = ['All', 'Cell Line', 'Plasmid', 'Reagent', 'Protein'];

  const filteredSamples = samples.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          s.barcode.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'All' || s.type === selectedType;
    return matchesSearch && matchesType;
  });

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    onCreateSample({
      name,
      type,
      projectId: 'PRJ-101',
      projectName: 'Cancer Research - Project 102',
      status: 'Available',
      location: {
        freezer: 'Freezer -20°C (Unit #2)',
        shelf: 'Shelf 1',
        rack: 'Rack A',
        box: 'Box 01',
        position: 'Slot 08'
      },
      barcode: `QR-${Math.floor(1000000 + Math.random() * 9000000)}`,
      createdDate: 'Just now',
      creator: 'Lead Researcher',
      quantity: qty || '5 Vials'
    });

    setName('');
    setQty('');
    setShowModal(false);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sample by ID, barcode, or name..."
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap ${
                selectedType === t
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {t}
            </button>
          ))}

          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors ml-2"
          >
            <Plus className="w-4 h-4" />
            <span>Register Sample</span>
          </button>
        </div>
      </div>

      {/* Samples Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Sample ID</th>
                <th className="py-3 px-4">Sample Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Project</th>
                <th className="py-3 px-4">Storage Location</th>
                <th className="py-3 px-4">Quantity</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredSamples.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-blue-600">{s.id}</td>
                  <td className="py-3 px-4 text-slate-800 font-semibold">{s.name}</td>
                  <td className="py-3 px-4">
                    <span className="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded text-[10px]">
                      {s.type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{s.projectName}</td>
                  <td className="py-3 px-4 text-slate-600 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                    <span className="truncate max-w-[180px]">{s.location.freezer} - {s.location.position}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{s.quantity}</td>
                  <td className="py-3 px-4">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      s.status === 'Available' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {s.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectSample(s.id)}
                      className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1 justify-end ml-auto"
                    >
                      <span>Inventory Detail</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Sample Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">Register Biological / Chemical Sample</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
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
                  value={type}
                  onChange={(e) => setType(e.target.value as any)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                >
                  <option value="Cell Line">Cell Line</option>
                  <option value="Plasmid">Plasmid</option>
                  <option value="Reagent">Reagent</option>
                  <option value="Protein">Protein</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Quantity / Volume</label>
                <input
                  type="text"
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                  placeholder="e.g. 10 Vials (1.5 mL each)"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-lg shadow-sm"
                >
                  Save Sample
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
