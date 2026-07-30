import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { Search, Plus, ArrowUpRight, Loader2, AlertCircle } from 'lucide-react';
import { useSequences, useCreateSequence } from '../../hooks/useSequences';
import { useAuth } from '../../providers/AuthProvider';

interface SequenceRegistryViewProps {
  onSelectSequence: (id: string) => void;
  onSelectView: (view: ViewMode) => void;
}

export const SequenceRegistryView: React.FC<SequenceRegistryViewProps> = ({
  onSelectSequence,
  onSelectView
}) => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: sequenceData, isLoading, error } = useSequences(
    page, pageSize, undefined, undefined, undefined, undefined, searchQuery
  );

  const createSequence = useCreateSequence();

  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [code, setCode] = useState(`SEQ-${Math.floor(1000 + Math.random() * 9000)}`);
  const [seqType, setSeqType] = useState('DNA');
  const [seqData, setSeqData] = useState('');

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !seqData.trim()) return;

    try {
      await createSequence.mutateAsync({
        sequence_code: code,
        sequence_name: name,
        sequence_type: seqType,
        sequence_data: seqData,
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        metadata_json: {},
      });
      setName('');
      setSeqData('');
      setCode(`SEQ-${Math.floor(1000 + Math.random() * 9000)}`);
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
              placeholder="Search Sequences..."
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Sequence</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12 h-full items-center">
           <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-12 h-full text-rose-500">
           <AlertCircle className="w-8 h-8 mb-4" />
           <span className="font-semibold">Failed to load sequences.</span>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Length</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {sequenceData?.items.map((seq) => (
                <tr key={seq.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-purple-600">{seq.sequence_code}</td>
                  <td className="py-3 px-4 text-slate-800 font-semibold">{seq.sequence_name}</td>
                  <td className="py-3 px-4 text-slate-600 font-bold">{seq.sequence_type}</td>
                  <td className="py-3 px-4 text-slate-600">{seq.length} bp</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectSequence(seq.id)}
                      className="text-xs font-semibold text-purple-600 hover:text-purple-700 flex items-center gap-1 justify-end ml-auto cursor-pointer"
                    >
                      <span>View</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {sequenceData?.items.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-slate-500">No sequences found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">New Sequence</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Code</label>
                <input type="text" required value={code} onChange={(e) => setCode(e.target.value)} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-purple-500 font-mono" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Name</label>
                <input type="text" required value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-purple-500" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Type</label>
                  <select value={seqType} onChange={(e) => setSeqType(e.target.value)} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-purple-500">
                    <option value="DNA">DNA</option>
                    <option value="RNA">RNA</option>
                    <option value="Protein">Protein</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Sequence Data</label>
                <textarea required value={seqData} onChange={(e) => setSeqData(e.target.value)} rows={4} className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-purple-500 font-mono uppercase" />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer">Cancel</button>
                <button type="submit" disabled={createSequence.isPending} className="px-4 py-2 text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white rounded-lg shadow-sm cursor-pointer disabled:opacity-50">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
