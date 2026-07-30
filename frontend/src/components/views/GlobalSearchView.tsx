import React, { useState } from 'react';
import { ViewMode } from '../../types';
import { Search, Filter, FlaskConical, TestTube2, Dna, FileText, Sparkles, ArrowUpRight } from 'lucide-react';

interface GlobalSearchViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
}

export const GlobalSearchView: React.FC<GlobalSearchViewProps> = ({
  onSelectView,
  onOpenExperiment
}) => {
  const [query, setQuery] = useState('CRISPR knockout efficiency in HEK293T');
  const [filter, setFilter] = useState('All');

  const filterTabs = ['All', 'Experiments', 'Samples', 'Sequences', 'Protocols'];

  const searchResults = [
    {
      id: 'EXP-2024-101',
      type: 'Experiment',
      title: 'CRISPR Knockout Validation in HEK293T',
      snippet: 'Knockout efficiency measured at 84.2% via gel electrophoresis band density analysis. T7 endonuclease cleavage confirmed double-strand break.',
      project: 'Cancer Research - Project 102',
      date: 'May 16, 2026',
      relevanceScore: '98% RAG Match'
    },
    {
      id: 'SMP-001024',
      type: 'Sample',
      title: 'HEK293T Cell Line (Passage 14)',
      snippet: 'Cryo-preserved cell line stock in Freezer -20°C (Unit #2), Shelf 2, Rack A, Slot 12.',
      project: 'Cancer Research - Project 102',
      date: 'May 10, 2026',
      relevanceScore: '94% Match'
    },
    {
      id: 'SEQ-9901',
      type: 'Sequence',
      title: 'Gene X - Homo sapiens (Target Locus)',
      snippet: 'Annotated CRISPR target region at 310-330 bp. GC Content: 52.4%, Length: 1,248 bp.',
      project: 'Cancer Research - Project 102',
      date: 'May 15, 2026',
      relevanceScore: '91% Match'
    }
  ];

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Search Input Hero Bar */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-600 animate-pulse" />
          <h2 className="text-lg font-bold text-slate-800">Global RAG Semantic Search</h2>
        </div>

        <div className="relative">
          <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask natural language questions or search by ID, gene, author..."
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-12 pr-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pt-1">
          {filterTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap ${
                filter === tab
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
        <span>Found {searchResults.length} relevant results across vector index</span>
        <span className="font-mono">RAG Embeddings: Qdrant / FAISS</span>
      </div>

      {/* Search Results List */}
      <div className="space-y-4">
        {searchResults.map((res) => (
          <div
            key={res.id}
            onClick={() => {
              if (res.type === 'Experiment') onOpenExperiment(res.id);
              if (res.type === 'Sample') onSelectView('samples');
              if (res.type === 'Sequence') onSelectView('sequences');
            }}
            className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition-all cursor-pointer space-y-2 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  res.type === 'Experiment' ? 'bg-blue-100 text-blue-700' :
                  res.type === 'Sample' ? 'bg-teal-100 text-teal-700' : 'bg-indigo-100 text-indigo-700'
                }`}>
                  {res.type}
                </span>
                <span className="font-mono text-xs font-bold text-slate-500">{res.id}</span>
                <span className="text-xs text-slate-400">• {res.project}</span>
              </div>
              <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                {res.relevanceScore}
              </span>
            </div>

            <h3 className="font-bold text-slate-800 text-base group-hover:text-blue-600 transition-colors flex items-center gap-2">
              <span>{res.title}</span>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed">{res.snippet}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
