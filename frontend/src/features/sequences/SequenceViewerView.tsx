import React, { useState } from 'react';
import type { SequenceRecord, ViewMode } from '../../types';
import { 
  Dna, Play, Download, CheckCircle2, Layers, Copy, 
  ChevronDown, RefreshCw, Eye, Sparkles, Code 
} from 'lucide-react';

interface SequenceViewerViewProps {
  sequence?: SequenceRecord;
  onSelectView: (view: ViewMode) => void;
}

export const SequenceViewerView: React.FC<SequenceViewerViewProps> = ({
  sequence,
  onSelectView
}) => {
  const [selectedSeqId, setSelectedSeqId] = useState<string>(sequence?.id || 'SEQ-9902');
  const [blastRunning, setBlastRunning] = useState(false);
  const [blastResult, setBlastResult] = useState<string | null>(null);
  const [showComplement, setShowComplement] = useState(false);
  const [copiedSeq, setCopiedSeq] = useState(false);
  const [activeTypeTab, setActiveTypeTab] = useState<'DNA' | 'RNA' | 'Protein'>('DNA');

  // Pre-loaded sequence records for switching in Section 7
  const sequences: SequenceRecord[] = [
    ...(sequence ? [sequence] : []),
    {
      id: 'SEQ-9902',
      name: 'pSpCas9(BB)-2A-PFP Vector Plasmid',
      organism: 'Synthetic Vector (SpCas9)',
      type: 'DNA',
      length: 4290,
      gcContent: 58.1,
      molecularWeightKgMol: 1320.5,
      createdDate: 'May 12, 2026',
      sequence: 
        'GAGTACCATGGCTCCAAAGAAGAAGCGTAAGGTCGGAATCCACGGGGTACCCGCCGCTGACAAGAAGTACAGCATCGGC' +
        'CTGGACATCGGCACCAACTCTGTGGGCTGGGCCGTGATCACCGACGAGTACAAGGTGCCCAGCAAGAAATTCAAGGTGC' +
        'TGGGCAACACCGACCGCCACAGCATCAAGAAGAACCTGATCGGAGCCCTGCTGTTCGACAGCGGCGAAACAGCCGAGGC' +
        'CACCCGGCTGAAGAGAACCGCCAGAAGAAGATACACCAGACGGAAGAACCGGATCTGCTATCTGCAAGAGATCTTCAGC',
      features: [
        { name: 'CBh Promoter', start: 1, end: 320, color: '#3B82F6' },
        { name: 'SpCas9 Nuclease', start: 321, end: 3800, color: '#10B981' },
        { name: '2A-PFP Tag', start: 3801, end: 4100, color: '#F59E0B' },
        { name: 'Ampicillin Resistance', start: 4101, end: 4290, color: '#EC4899' }
      ]
    },
    {
      id: 'SEQ-9903',
      name: 'SARS-CoV-2 Spike Glycoprotein mRNA',
      organism: 'Severe acute respiratory syndrome coronavirus 2',
      type: 'RNA',
      length: 1273,
      gcContent: 48.6,
      molecularWeightKgMol: 412.8,
      createdDate: 'May 08, 2026',
      sequence: 
        'AUGUUUGUUUUUCUUGUUUUAUUGCCACUAGUCUCUAGUCAGUGUGUUAAUCUUACAACCAGAACUCAAUUACCCCCUG' +
        'CAUACACUAAUUCUUUCACACGUGGUGUUUAUUACCCUGACAAAGUUUUCAGAUCCUCAGUUUUACAUUCAACUCAGGA' +
        'CUUGUUCUUACCUUUCUUUUCCAAUGUUACUUGGUUCCAUGCUAUACAUGUCUCUGGGACCAAUGGUACUAAGAGGUUU',
      features: [
        { name: '5\' UTR Leader', start: 1, end: 80, color: '#6366F1' },
        { name: 'Signal Peptide', start: 81, end: 240, color: '#14B8A6' },
        { name: 'RBD Domain', start: 241, end: 950, color: '#8B5CF6' },
        { name: 'Poly(A) Tail', start: 951, end: 1273, color: '#F43F5E' }
      ]
    }
  ];

  const currentSeqRecord = sequences.find(s => s.id === selectedSeqId) || sequences[0];

  const handleRunBlast = () => {
    setBlastRunning(true);
    setBlastResult(null);

    setTimeout(() => {
      setBlastRunning(false);
      setBlastResult(`NCBI BLAST Alignment Complete: 99.8% identity match to ${currentSeqRecord.organism} (E-value: 0.0, Bit score: 2410).`);
    }, 1200);
  };

  const handleCopySeq = () => {
    navigator.clipboard.writeText(currentSeqRecord.sequence);
    setCopiedSeq(true);
    setTimeout(() => setCopiedSeq(false), 2000);
  };

  const getComplementBase = (base: string) => {
    switch (base) {
      case 'A': return 'T';
      case 'T': return 'A';
      case 'U': return 'A';
      case 'C': return 'G';
      case 'G': return 'C';
      default: return base;
    }
  };

  const sequenceLines: string[] = [];
  for (let i = 0; i < currentSeqRecord.sequence.length; i += 60) {
    sequenceLines.push(currentSeqRecord.sequence.slice(i, i + 60));
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Sequence Header & Selector Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold shadow-md shadow-blue-500/20">
            <Dna className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
              <span className="text-blue-600 font-semibold">DNA / RNA / Protein Sequence Viewer</span>
              <span>•</span>
              <span className="font-mono font-bold text-slate-700">{currentSeqRecord.id}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">{currentSeqRecord.name}</h2>
            <p className="text-xs text-slate-500">{currentSeqRecord.organism}</p>
          </div>
        </div>

        {/* Controls: Sequence Switcher & BLAST Runner */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <select
              value={selectedSeqId}
              onChange={(e) => setSelectedSeqId(e.target.value)}
              className="bg-slate-100 border border-slate-200 text-slate-800 text-xs font-semibold rounded-xl px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer appearance-none"
            >
              {sequences.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id}: {s.name} ({s.type})
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>

          <button
            onClick={handleRunBlast}
            disabled={blastRunning}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {blastRunning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>{blastRunning ? 'Running BLAST...' : 'Run BLAST Alignment'}</span>
          </button>

          <button
            onClick={handleCopySeq}
            className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-xl transition-colors cursor-pointer"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>{copiedSeq ? 'Copied!' : 'Copy Sequence'}</span>
          </button>
        </div>
      </div>

      {/* Metrics Bar & Sequence Type Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4.5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 font-medium">Sequence Length</p>
            <p className="text-xl font-bold text-slate-900 mt-1 font-mono">{currentSeqRecord.length} bp</p>
          </div>
          <Code className="w-6 h-6 text-slate-400" />
        </div>

        <div className="bg-white p-4.5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 font-medium">GC Content Ratio</p>
            <p className="text-xl font-bold text-blue-600 mt-1 font-mono">{currentSeqRecord.gcContent}%</p>
          </div>
          <Sparkles className="w-6 h-6 text-blue-500" />
        </div>

        <div className="bg-white p-4.5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 font-medium">Molecular Weight</p>
            <p className="text-xl font-bold text-emerald-600 mt-1 font-mono">{currentSeqRecord.molecularWeightKgMol} kDa</p>
          </div>
          <Dna className="w-6 h-6 text-emerald-500" />
        </div>

        <div className="bg-white p-4.5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 font-medium">Annotated Features</p>
            <p className="text-xl font-bold text-indigo-600 mt-1 font-mono">{currentSeqRecord.features.length} Regions</p>
          </div>
          <Layers className="w-6 h-6 text-indigo-500" />
        </div>
      </div>

      {/* BLAST Alignment Result Banner */}
      {blastResult && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-2xl text-xs text-blue-900 font-semibold flex items-center gap-2.5 shadow-sm">
          <CheckCircle2 className="w-5 h-5 text-blue-600 shrink-0" />
          <span>{blastResult}</span>
        </div>
      )}

      {/* Sequence Feature Annotation Map */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            <span>Interactive Sequence Feature Map</span>
          </h4>
          <span className="text-[11px] text-slate-500">1 — {currentSeqRecord.length} bp</span>
        </div>

        {/* Visual Map Bar */}
        <div className="h-4 bg-slate-100 rounded-full overflow-hidden flex relative border border-slate-200">
          {currentSeqRecord.features.map((feat, idx) => {
            const widthPct = ((feat.end - feat.start) / currentSeqRecord.length) * 100;
            return (
              <div
                key={idx}
                style={{ width: `${widthPct}%`, backgroundColor: feat.color }}
                className="h-full transition-opacity hover:opacity-80 cursor-pointer"
                title={`${feat.name} (${feat.start}-${feat.end} bp)`}
              />
            );
          })}
        </div>

        {/* Feature Tags Legend */}
        <div className="flex flex-wrap gap-2.5 pt-1">
          {currentSeqRecord.features.map((feat, idx) => (
            <div key={idx} className="flex items-center gap-2 text-xs bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 shadow-2xs">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: feat.color }}></span>
              <span className="font-bold text-slate-800">{feat.name}</span>
              <span className="text-slate-500 font-mono text-[11px]">({feat.start}–{feat.end} bp)</span>
            </div>
          ))}
        </div>
      </div>

      {/* FASTA Nucleotide Rendering Box */}
      <div className="bg-slate-900 rounded-3xl p-6 shadow-2xl space-y-4 font-mono text-xs border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-slate-400 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <span className="text-white font-bold tracking-wide">FASTA Sequence Renderer</span>
            <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-xl text-[11px]">
              <button
                onClick={() => setShowComplement(false)}
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${!showComplement ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                Sense (5' → 3')
              </button>
              <button
                onClick={() => setShowComplement(true)}
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${showComplement ? 'bg-teal-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                Complement (3' → 5')
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3 text-[11px]">
            <span className="text-red-400 font-bold">● Adenine (A)</span>
            <span className="text-blue-400 font-bold">● Thymine/Uracil (T/U)</span>
            <span className="text-emerald-400 font-bold">● Cytosine (C)</span>
            <span className="text-amber-400 font-bold">● Guanine (G)</span>
          </div>
        </div>

        {/* Monospace Code Viewport */}
        <div className="space-y-2 overflow-x-auto text-slate-200 leading-relaxed max-h-[420px] overflow-y-auto pr-2">
          {sequenceLines.map((line, idx) => {
            const startBp = idx * 60 + 1;
            const displayedLine = showComplement 
              ? line.split('').map(getComplementBase).join('') 
              : line;

            return (
              <div key={idx} className="flex items-center gap-4 hover:bg-slate-800/50 p-1 rounded transition-colors">
                <span className="text-slate-500 w-12 text-right select-none text-[11px] font-bold">{startBp}</span>
                <div className="tracking-widest space-x-1">
                  {displayedLine.split('').map((char, charIdx) => {
                    let colorStyle = 'text-slate-200';
                    if (char === 'A') colorStyle = 'bg-red-950/80 text-red-400 px-1 rounded font-bold';
                    if (char === 'T' || char === 'U') colorStyle = 'bg-blue-950/80 text-blue-400 px-1 rounded font-bold';
                    if (char === 'C') colorStyle = 'bg-emerald-950/80 text-emerald-400 px-1 rounded font-bold';
                    if (char === 'G') colorStyle = 'bg-amber-950/80 text-amber-400 px-1 rounded font-bold';
                    return <span key={charIdx} className={colorStyle}>{char}</span>;
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

