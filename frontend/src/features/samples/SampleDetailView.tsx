import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { 
  ArrowLeft, QrCode, MapPin, History, Copy, Download, 
  Dna, FlaskConical, ChevronDown, Check, Tag, ShieldCheck, Box, Loader2, AlertCircle
} from 'lucide-react';
import { useSample, useUpdateSample } from '../../hooks/useSamples';

interface SampleDetailViewProps {
  sampleId: string;
  onSelectSample: (sampleId: string) => void;
  onSelectView: (view: ViewMode) => void;
}

export const SampleDetailView: React.FC<SampleDetailViewProps> = ({
  sampleId,
  onSelectSample,
  onSelectView
}) => {
  const { data: sample, isLoading, error } = useSample(sampleId);
  const updateSample = useUpdateSample();

  const [selectedSlot, setSelectedSlot] = useState<number>(12);
  const [copiedBarcode, setCopiedBarcode] = useState(false);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [checkoutVolume, setCheckoutVolume] = useState('1');

  const slots = Array.from({ length: 81 }, (_, i) => i + 1);

  const handleCopyBarcode = () => {
    if (!sample) return;
    navigator.clipboard.writeText(sample.barcode);
    setCopiedBarcode(true);
    setTimeout(() => setCopiedBarcode(false), 2000);
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!sample) return;
    await updateSample.mutateAsync({
      id: sample.id,
      data: { status: newStatus }
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center p-12 h-full items-center">
         <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    );
  }

  if (error || !sample) {
    return (
      <div className="flex flex-col items-center justify-center p-12 h-full text-rose-500">
         <AlertCircle className="w-8 h-8 mb-4" />
         <span className="font-semibold">Failed to load sample details.</span>
      </div>
    );
  }

  // Derive from metadata_json or backend schemas
  const chainOfCustody = sample.chain_of_custody || sample.metadata_json?.chainOfCustody || [];
  const locationString = sample.metadata_json?.locationString || 'Unassigned';

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectView('samples')}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-mono">{sample.sample_code}</span>
              <span>/</span>
              <span className="bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded">{sample.metadata_json?.typeCode || 'UNKNOWN'}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{sample.sample_name}</h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition-colors cursor-pointer">
            <QrCode className="w-4 h-4 text-slate-600" />
            <span>Print Label</span>
          </button>
          
          <select
            value={sample.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            disabled={updateSample.isPending}
            className="bg-slate-50 border border-slate-200 text-xs font-bold rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 cursor-pointer disabled:opacity-50"
          >
            <option value="available">Available</option>
            <option value="consumed">Consumed</option>
            <option value="expired">Expired</option>
          </select>

          <button
            onClick={() => setShowCheckoutModal(true)}
            className="flex items-center gap-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer"
          >
            <FlaskConical className="w-4 h-4" />
            <span>Check Out Aliquot</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Metadata & Audit */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-3 mb-4">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Sample Identity & Properties</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 text-sm">
              <div className="space-y-1">
                <span className="text-slate-400 text-xs font-medium">Barcode (Global ID)</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-slate-800">{sample.barcode}</span>
                  <button onClick={handleCopyBarcode} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                    {copiedBarcode ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs font-medium">Project Source</span>
                <p className="font-semibold text-blue-600 cursor-pointer hover:underline">{sample.experiment_id}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs font-medium">Available Quantity</span>
                <p className="font-bold text-slate-800 text-lg">{sample.quantity} {sample.unit}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs font-medium">Date Registered</span>
                <p className="font-semibold text-slate-800">{new Date(sample.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-3 mb-4">
              <History className="w-4 h-4 text-blue-600" />
              <span>Chain of Custody (Audit Trail)</span>
            </h3>

            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
              {chainOfCustody.map((audit: any, i: number) => (
                <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-4 h-4 rounded-full border-2 border-white bg-blue-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2"></div>
                  <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] bg-slate-50 p-3 rounded-lg border border-slate-200 shadow-sm text-xs">
                    <div className="flex justify-between font-bold text-slate-800 mb-1">
                      <span>{audit.action}</span>
                      <span className="text-slate-400 text-[10px]">{audit.performed_at}</span>
                    </div>
                    <p className="text-slate-600">{audit.custodian_id} - {audit.remarks}</p>
                  </div>
                </div>
              ))}
              {chainOfCustody.length === 0 && <p className="text-xs text-slate-400 pl-4 py-2">No custody events recorded.</p>}
            </div>
          </div>
        </div>

        {/* Right Column - Location Tracker */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <MapPin className="w-4 h-4 text-rose-500" />
                <span>Physical Location</span>
              </h3>
            </div>
            
            <div className="p-5 space-y-4">
              <div className="bg-blue-50/50 p-3 rounded-xl border border-blue-100/50 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Freezer Unit</span>
                  <span className="font-bold text-slate-800">{locationString}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Temperature</span>
                  <span className="font-bold text-blue-600">{sample.storage_temperature}</span>
                </div>
              </div>

              <div className="pt-2">
                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="font-semibold text-slate-700">Box Map (9x9)</span>
                  <span className="text-slate-400 font-mono">Pos: A{selectedSlot}</span>
                </div>

                <div className="grid grid-cols-9 gap-1 aspect-square bg-slate-100 p-2 rounded-xl border border-slate-200">
                  {slots.map(s => (
                    <button
                      key={s}
                      onClick={() => setSelectedSlot(s)}
                      className={`rounded-sm transition-colors ${
                        s === selectedSlot ? 'bg-rose-500 ring-2 ring-rose-300 ring-offset-1' :
                        s % 12 === 0 ? 'bg-teal-400' : 
                        s % 5 === 0 ? 'bg-amber-400' : 'bg-white hover:bg-slate-200'
                      }`}
                    ></button>
                  ))}
                </div>
                
                <div className="flex justify-center gap-4 mt-3 text-[10px] text-slate-500 font-medium">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span> This Sample</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-teal-400"></span> My Samples</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400"></span> Reserved</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      {showCheckoutModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">Check Out Aliquot</h3>
            <p className="text-xs text-slate-600">Checking out material logs a chain-of-custody event and decrements available inventory.</p>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Volume / Quantity to Extract</label>
                <input
                  type="number"
                  value={checkoutVolume}
                  onChange={(e) => setCheckoutVolume(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-teal-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowCheckoutModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  alert('Checked out successfully (simulated API)');
                  setShowCheckoutModal(false);
                }}
                className="px-4 py-2 text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-lg shadow-sm cursor-pointer"
              >
                Confirm Extraction
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
