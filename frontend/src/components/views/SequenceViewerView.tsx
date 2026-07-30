import React, { useState } from 'react';
import { SequenceRecord, ViewMode } from '../../types';
import { Dna, Play, Download, Search, Sparkles, Filter, CheckCircle2, Layers } from 'lucide-react';

interface SequenceViewerViewProps {
  sequence: SequenceRecord;
  onSelectView: (view: ViewMode) => void;
}

export const SequenceViewerView: React.FC<SequenceViewerViewProps> = ({
  sequence,
  onSelectView
}) => {
  const [blastRunning, setBlastRunning] = useState(false);
  const [blastResult, setBlastResult] = useState<string | null>(null);

  const handleRunBlast = () => {
    setBlastRunning(true);
    setBlastResult(null);

    setTimeout(() => {
      setBlastRunning(false);
      setBlastResult('NCBI BLAST Result: 99.8% identity match to Homo sapiens chromosome 14, GRCh38.p14 primary assembly (E-value: 0.0).');
    }, 1500);
  };

  // Format sequence into lines of 60 nucleotides
  const sequenceLines: string[] = [];
  for (let i = 0; i < sequence.sequence.length; i += 60) {
    sequenceLines.push(sequence.sequence.slice(i, i + 60));
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Sequence Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold shadow-md shadow-blue-500/20">
            <Dna className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Sequence Registry</span>
              <span>/</span>
              <span className="font-mono">{sequence.id}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">{sequence.name}</h2>
            <p className="text-xs text-slate-500">{sequence.organism}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunBlast}
            disabled={blastRunning}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{blastRunning ? 'Running NCBI BLAST...' : 'Run BLAST Alignment'}</span>
          </button>
          <button className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition-colors">
            <Download className="w-3.5 h-3.5" />
            <span>Export FASTA</span>
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Sequence Length</p>
          <p className="text-xl font-bold text-slate-800 mt-1 font-mono">{sequence.length} bp</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">GC Content %</p>
          <p className="text-xl font-bold text-blue-600 mt-1 font-mono">{sequence.gcContent}%</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Molecular Weight</p>
          <p className="text-xl font-bold text-emerald-600 mt-1 font-mono">{sequence.molecularWeightKgMol} kDa</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Annotated Features</p>
          <p className="text-xl font-bold text-indigo-600 mt-1 font-mono">{sequence.features.length} Regions</p>
        </div>
      </div>

      {blastResult && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800 font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
          <span>{blastResult}</span>
        </div>
      )}

      {/* Feature Map Legend */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-4 h-4 text-indigo-600" />
          <span>Sequence Features Map</span>
        </h4>
        <div className="flex flex-wrap gap-3 pt-1">
          {sequence.features.map((feat, idx) => (
            <div key={idx} className="flex items-center gap-2 text-xs bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: feat.color }}></span>
              <span className="font-semibold text-slate-800">{feat.name}</span>
              <span className="text-slate-500 font-mono text-[11px]">({feat.start}-{feat.end} bp)</span>
            </div>
          ))}
        </div>
      </div>

      {/* Nucleotide Sequence Viewer Grid */}
      <div className="bg-slate-900 rounded-2xl p-6 shadow-xl space-y-4 font-mono text-xs">
        <div className="flex justify-between items-center text-slate-400 border-b border-slate-800 pb-3">
          <span className="text-slate-300 font-bold">FASTA Sequence Rendering</span>
          <div className="flex items-center gap-3">
            <span className="text-red-400">● A</span>
            <span className="text-blue-400">● T</span>
            <span className="text-emerald-400">● C</span>
            <span className="text-amber-400">● G</span>
          </div>
        </div>

        <div className="space-y-2 overflow-x-auto text-slate-200 leading-relaxed">
          {sequenceLines.map((line, idx) => {
            const startBp = idx * 60 + 1;
            return (
              <div key={idx} className="flex items-center gap-4">
                <span className="text-slate-500 w-12 text-right select-none">{startBp}</span>
                <div className="tracking-widest space-x-0.5">
                  {line.split('').map((char, charIdx) => {
                    let colorClass = 'text-slate-200';
                    if (char === 'A') colorClass = 'nucleotide-A px-0.5 rounded';
                    if (char === 'T') colorClass = 'nucleotide-T px-0.5 rounded';
                    if (char === 'C') colorClass = 'nucleotide-C px-0.5 rounded';
                    if (char === 'G') colorClass = 'nucleotide-G px-0.5 rounded';
                    return <span key={charIdx} className={colorClass}>{char}</span>;
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
