import React from 'react';
import { Sample, ViewMode } from '../../types';
import { ArrowLeft, QrCode, MapPin, Calendar, User, History, CheckCircle2, Copy, Download } from 'lucide-react';

interface SampleDetailViewProps {
  sample: Sample;
  onSelectView: (view: ViewMode) => void;
}

export const SampleDetailView: React.FC<SampleDetailViewProps> = ({
  sample,
  onSelectView
}) => {
  // Generate simulated 9x9 Freezer Box Grid
  const slots = Array.from({ length: 81 }, (_, i) => i + 1);
  const activeSlotIndex = 12; // Slot 12 highlighted!

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectView('samples')}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Sample Registry</span>
              <span>/</span>
              <span className="font-mono font-bold text-teal-600">{sample.id}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800">{sample.name}</h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs bg-emerald-100 text-emerald-800 font-bold px-3 py-1 rounded-full">
            {sample.status}
          </span>
        </div>
      </div>

      {/* Main Grid: Details + Freezer Storage Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Sample Info & QR Code */}
        <div className="space-y-6">
          
          {/* Metadata Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm border-b border-slate-100 pb-2">
              Sample Specifications
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Type</span>
                <span className="font-semibold text-slate-800">{sample.type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Project</span>
                <span className="font-semibold text-slate-800">{sample.projectName}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Quantity Remaining</span>
                <span className="font-semibold text-slate-800">{sample.quantity}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Registered By</span>
                <span className="font-semibold text-slate-800">{sample.creator}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Registration Date</span>
                <span className="font-semibold text-slate-800">{sample.createdDate}</span>
              </div>
            </div>
          </div>

          {/* Barcode & QR Code Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm text-center space-y-3">
            <h3 className="font-bold text-slate-800 text-sm">Chain-of-Custody Barcode</h3>
            
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex flex-col items-center justify-center space-y-2">
              <div className="w-28 h-28 bg-slate-900 text-white flex items-center justify-center rounded-lg shadow-inner font-mono text-xs font-bold p-2 text-center">
                <div className="border-4 border-white p-2 w-full h-full flex items-center justify-center bg-white text-slate-900">
                  <QrCode className="w-20 h-20 text-slate-900" />
                </div>
              </div>
              <span className="font-mono text-xs font-bold text-slate-800 tracking-wider">{sample.barcode}</span>
            </div>

            <div className="flex gap-2">
              <button className="flex-1 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1">
                <Copy className="w-3.5 h-3.5" />
                <span>Copy ID</span>
              </button>
              <button className="flex-1 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1">
                <Download className="w-3.5 h-3.5" />
                <span>Print QR</span>
              </button>
            </div>
          </div>

        </div>

        {/* Right Column: Freezer Box Grid Mapping (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Freezer Location Header */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-800 text-base flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-teal-600" />
                  <span>Freezer Box Storage Grid</span>
                </h3>
                <p className="text-xs text-slate-500">
                  {sample.location.freezer} → {sample.location.shelf} → {sample.location.rack} → {sample.location.box}
                </p>
              </div>
              <span className="bg-blue-50 text-blue-700 border border-blue-200 font-mono text-xs font-bold px-3 py-1 rounded-lg">
                Target: {sample.location.position}
              </span>
            </div>

            {/* 9x9 Storage Box Grid */}
            <div className="bg-slate-900 p-4 rounded-xl space-y-3">
              <div className="flex justify-between items-center text-xs text-slate-300 font-mono">
                <span>Box 04 (9x9 Cryo Rack)</span>
                <span className="text-emerald-400">● Slot 12 Occupied</span>
              </div>

              <div className="grid grid-cols-9 gap-1.5">
                {slots.map((slotNum) => {
                  const isCurrent = slotNum === activeSlotIndex;
                  const isOccupiedRandom = (slotNum * 7) % 3 === 0;

                  return (
                    <div
                      key={slotNum}
                      className={`h-8 rounded flex items-center justify-center font-mono text-[10px] transition-all ${
                        isCurrent
                          ? 'bg-emerald-500 text-white font-bold ring-4 ring-emerald-400/40 animate-pulse'
                          : isOccupiedRandom
                          ? 'bg-slate-700 text-slate-400'
                          : 'bg-slate-800 text-slate-600 border border-slate-700/50'
                      }`}
                    >
                      {slotNum}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Usage History Log */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
              <History className="w-4 h-4 text-blue-600" />
              <span>Chain-of-Custody Usage History</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-800">Checked out 2.5 x 10^6 cells for EXP-2024-101</p>
                  <p className="text-slate-500 text-[11px]">By Dr. Sarah Johnson • May 16, 2026, 10:14 AM</p>
                </div>
                <span className="text-[10px] bg-emerald-100 text-emerald-700 font-bold px-2 py-0.5 rounded">Checked Out</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-800">Sample Registration & Freezer Placement</p>
                  <p className="text-slate-500 text-[11px]">By Lead Researcher • May 10, 2026, 09:30 AM</p>
                </div>
                <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded">Registered</span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
