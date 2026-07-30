import React, { useState, useMemo } from 'react';
import type { ViewMode } from '../../types';
import { Search, Sparkles, ArrowUpRight, X, Filter, FileText, TestTube2, Dna, FlaskConical } from 'lucide-react';

interface GlobalSearchViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
  onSelectSample?: (sampleId: string) => void;
}

interface SearchItem {
  id: string;
  type: 'Experiment' | 'Sample' | 'Sequence' | 'Protocol';
  title: string;
  snippet: string;
  project: string;
  date: string;
  authorOrCreator: string;
  tags: string[];
  relevanceScore: number;
}

export const GlobalSearchView: React.FC<GlobalSearchViewProps> = ({
  onSelectView,
  onOpenExperiment,
  onSelectSample
}) => {
  const [query, setQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<string>('All');

  const filterTabs = ['All', 'Experiments', 'Samples', 'Sequences', 'Protocols'];

  const suggestedQueries = [
    'CRISPR Knockout',
    'HEK293T Cell Line',
    'Gene X DNA',
    'Lipofectamine 3000',
    'Western Blotting',
    'PCR Annealing'
  ];

  // Master RAG Index Dataset with items across all categories
  const allKnowledgeItems: SearchItem[] = useMemo(() => [
    // Experiments
    {
      id: 'EXP-2024-101',
      type: 'Experiment',
      title: 'CRISPR Knockout Validation in HEK293T',
      snippet: 'Knockout efficiency measured at 84.2% via gel electrophoresis band density analysis. T7 endonuclease cleavage confirmed double-strand break at locus 142.',
      project: 'Cancer Research - Project 102',
      date: 'May 16, 2026',
      authorOrCreator: 'Dr. Sarah Johnson',
      tags: ['CRISPR', 'HEK293T', 'Gene Editing', 'T7 Assay'],
      relevanceScore: 98
    },
    {
      id: 'EXP-2024-102',
      type: 'Experiment',
      title: 'PCR Primers Optimization for Gene X',
      snippet: 'Determine optimal annealing temperature gradient for primer set GX-F2 / GX-R2. Sharp single bands observed at annealing temperature of 60.5°C.',
      project: 'Cancer Research - Project 102',
      date: 'May 15, 2026',
      authorOrCreator: 'Lead Scientist',
      tags: ['PCR', 'Primers', 'Optimization'],
      relevanceScore: 95
    },
    {
      id: 'EXP-2024-103',
      type: 'Experiment',
      title: 'Western Blotting of Target Kinase Expression',
      snippet: 'Quantify kinase phosphorylation state following neurotrophic factor stimulation. RIPA buffer lysis, BCA protein quantification, 10% SDS-PAGE gel.',
      project: 'Neurobiology - Synapse Study',
      date: 'May 14, 2026',
      authorOrCreator: 'Dr. Sarah Johnson',
      tags: ['Western Blot', 'Kinase', 'Neuroscience'],
      relevanceScore: 92
    },
    {
      id: 'EXP-2024-104',
      type: 'Experiment',
      title: 'Lipid Nanoparticle Encapsulation Efficiency Assay',
      snippet: 'Optimizing LNP formulation for mRNA delivery using dynamic light scattering and fluorescent dye binding.',
      project: 'Vaccine Development - mRNA',
      date: 'May 10, 2026',
      authorOrCreator: 'Ashwin',
      tags: ['mRNA', 'LNP', 'Nanoparticle'],
      relevanceScore: 89
    },

    // Samples
    {
      id: 'SMP-001024',
      type: 'Sample',
      title: 'HEK293T Cell Line (Passage 14)',
      snippet: 'Cryo-preserved cell line stock in Freezer -20°C (Unit #2), Shelf 2, Rack A, Box 04, Slot 12. 12 Vials remaining.',
      project: 'Cancer Research - Project 102',
      date: 'May 10, 2026',
      authorOrCreator: 'Dr. Sarah Johnson',
      tags: ['Cell Line', 'HEK293T', 'Freezer Storage'],
      relevanceScore: 94
    },
    {
      id: 'SMP-001025',
      type: 'Sample',
      title: 'pSpCas9(BB)-2A-PFP Plasmid Vector',
      snippet: 'High-purity Cas9 expression plasmid stock stored in Freezer -80°C (Cryo #1), Rack B, Box 02, Slot 04. 450 ug (1.2 ug/uL).',
      project: 'Cancer Research - Project 102',
      date: 'Apr 28, 2026',
      authorOrCreator: 'Lead Scientist',
      tags: ['Plasmid', 'Cas9', 'Vector'],
      relevanceScore: 91
    },
    {
      id: 'SMP-001026',
      type: 'Sample',
      title: 'BSA Serum & Lipofectamine 3000 Reagent',
      snippet: 'Reagent stock in Refrigerator 4°C, Shelf 3. Lipofectamine 3000 transfection kit lot L3K-8812.',
      project: 'Neurobiology - Synapse Study',
      date: 'May 01, 2026',
      authorOrCreator: 'Raj',
      tags: ['Reagent', 'BSA', 'Lipofectamine'],
      relevanceScore: 88
    },
    {
      id: 'SMP-001027',
      type: 'Sample',
      title: 'Target Kinase Protein Lysate - Trial B',
      snippet: 'Purified protein lysate stored in Liquid Nitrogen Tank #1, Canister 2, Rack C, Slot 18. 80 uL (4.5 mg/mL).',
      project: 'Vaccine Development - mRNA',
      date: 'May 12, 2026',
      authorOrCreator: 'Ashwin',
      tags: ['Protein', 'Lysate', 'Cryo'],
      relevanceScore: 86
    },

    // Sequences
    {
      id: 'SEQ-9901',
      type: 'Sequence',
      title: 'Gene X - Homo sapiens (Target Locus DNA)',
      snippet: 'Annotated CRISPR target locus at 310-330 bp in Exon 1. GC Content: 52.4%, Length: 1,248 bp, Molecular Weight: 384.2 kDa.',
      project: 'Cancer Research - Project 102',
      date: 'May 15, 2026',
      authorOrCreator: 'Homo sapiens (Human)',
      tags: ['DNA', 'Gene X', 'CRISPR Target'],
      relevanceScore: 96
    },
    {
      id: 'SEQ-9902',
      type: 'Sequence',
      title: 'pSpCas9(BB)-2A-PFP Vector Plasmid Sequence',
      snippet: 'Synthetic vector plasmid sequence with CBh promoter, SpCas9 nuclease CDS, 2A-PFP tag, and ampicillin resistance gene.',
      project: 'Cancer Research - Project 102',
      date: 'May 12, 2026',
      authorOrCreator: 'Synthetic Vector',
      tags: ['DNA', 'Plasmid', 'SpCas9'],
      relevanceScore: 90
    },
    {
      id: 'SEQ-9903',
      type: 'Sequence',
      title: 'SARS-CoV-2 Spike Glycoprotein mRNA Sequence',
      snippet: 'Codon-optimized mRNA sequence encoding SARS-CoV-2 spike glycoprotein with 5\' UTR leader and poly(A) tail.',
      project: 'Vaccine Development - mRNA',
      date: 'May 08, 2026',
      authorOrCreator: 'Viral Genome',
      tags: ['RNA', 'Spike mRNA', 'Vaccine'],
      relevanceScore: 87
    },

    // Protocols
    {
      id: 'SOP-MB-2026-09',
      type: 'Protocol',
      title: 'High-Efficiency Lipofectamine 3000 Transfection SOP',
      snippet: 'Standard Operating Procedure: 5-step transfection protocol for 6-well plates. Seed cells at 0.5x10^6 cells/well in DMEM + 10% FBS.',
      project: 'Standard Operating Procedures',
      date: 'May 16, 2026',
      authorOrCreator: 'AI Copilot RAG Engine',
      tags: ['SOP', 'Transfection', 'Protocol'],
      relevanceScore: 97
    },
    {
      id: 'SOP-PCR-2026-02',
      type: 'Protocol',
      title: 'Gradient PCR Thermocycling & Primer Design SOP',
      snippet: 'SOP detailing master mix preparation, thermal cycler gradient setup (55°C to 65°C), 35-cycle amplification, and gel analysis.',
      project: 'Standard Operating Procedures',
      date: 'May 14, 2026',
      authorOrCreator: 'Dr. Sarah Johnson',
      tags: ['SOP', 'PCR', 'Thermocycling'],
      relevanceScore: 93
    },
    {
      id: 'SOP-WB-2026-05',
      type: 'Protocol',
      title: 'RIPA Cell Lysis & Western Blot Immunodetection SOP',
      snippet: 'SOP for primary neuron lysis, BCA protein assay quantification, SDS-PAGE gel transfer to PVDF, and antibody chemiluminescence detection.',
      project: 'Standard Operating Procedures',
      date: 'May 11, 2026',
      authorOrCreator: 'Lead Scientist',
      tags: ['SOP', 'Western Blot', 'Immunodetection'],
      relevanceScore: 91
    }
  ], []);

  // Dynamic Filtering Algorithm
  const filteredResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    
    return allKnowledgeItems.filter((item) => {
      // Tab category filter: 'All' matches everything, otherwise match specific type
      if (selectedFilter === 'Experiments' && item.type !== 'Experiment') return false;
      if (selectedFilter === 'Samples' && item.type !== 'Sample') return false;
      if (selectedFilter === 'Sequences' && item.type !== 'Sequence') return false;
      if (selectedFilter === 'Protocols' && item.type !== 'Protocol') return false;

      // Text query match: if empty, include all items for selected filter tab
      if (!q) return true;

      const inTitle = item.title.toLowerCase().includes(q);
      const inSnippet = item.snippet.toLowerCase().includes(q);
      const inId = item.id.toLowerCase().includes(q);
      const inProject = item.project.toLowerCase().includes(q);
      const inAuthor = item.authorOrCreator.toLowerCase().includes(q);
      const inTags = item.tags.some(t => t.toLowerCase().includes(q));

      return inTitle || inSnippet || inId || inProject || inAuthor || inTags;
    });
  }, [query, selectedFilter, allKnowledgeItems]);

  const handleItemClick = (res: SearchItem) => {
    if (res.type === 'Experiment') {
      onOpenExperiment(res.id);
    } else if (res.type === 'Sample') {
      if (onSelectSample) {
        onSelectSample(res.id);
      } else {
        onSelectView('sample-detail');
      }
    } else if (res.type === 'Sequence') {
      onSelectView('sequences');
    } else if (res.type === 'Protocol') {
      onSelectView('eln');
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Search Input Hero Bar */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 animate-pulse" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Global RAG Semantic Search</h2>
          </div>
          <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
            Vector Index: Qdrant RAG
          </span>
        </div>

        {/* Input Bar with Clear Action */}
        <div className="relative">
          <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask natural language questions or search by ID, gene, cell line, protocol..."
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-12 pr-10 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium transition-all"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-3 top-3.5 text-slate-400 hover:text-slate-600 p-0.5 rounded-full hover:bg-slate-200 transition-colors cursor-pointer"
              title="Clear search query"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Suggested Search Query Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pt-1">
          <span className="text-[11px] font-bold text-slate-400 shrink-0">Suggestions:</span>
          {suggestedQueries.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(sq)}
              className="text-xs bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-300 px-3 py-1 rounded-lg whitespace-nowrap transition-colors font-medium cursor-pointer"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Filter Category Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pt-2 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-400 shrink-0 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Filter:
          </span>
          {filterTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setSelectedFilter(tab)}
              className={`text-xs font-bold px-3.5 py-1.5 rounded-lg transition-all whitespace-nowrap cursor-pointer ${
                selectedFilter === tab
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Results Count Header */}
      <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
        <span>Found <strong className="text-slate-800 font-bold">{filteredResults.length}</strong> matching entry{filteredResults.length !== 1 ? 's' : ''} in lab database</span>
        <span className="font-mono text-[11px]">Real-time RAG Search Active</span>
      </div>

      {/* Search Results Feed */}
      <div className="space-y-4">
        {filteredResults.length > 0 ? (
          filteredResults.map((res) => (
            <div
              key={res.id}
              onClick={() => handleItemClick(res)}
              className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-blue-400 hover:shadow-md transition-all cursor-pointer space-y-3 group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                    res.type === 'Experiment' ? 'bg-blue-100 text-blue-800' :
                    res.type === 'Sample' ? 'bg-teal-100 text-teal-800' :
                    res.type === 'Sequence' ? 'bg-indigo-100 text-indigo-800' : 'bg-purple-100 text-purple-800'
                  }`}>
                    {res.type === 'Experiment' && <FlaskConical className="w-3 h-3" />}
                    {res.type === 'Sample' && <TestTube2 className="w-3 h-3" />}
                    {res.type === 'Sequence' && <Dna className="w-3 h-3" />}
                    {res.type === 'Protocol' && <FileText className="w-3 h-3" />}
                    <span>{res.type}</span>
                  </span>
                  <span className="font-mono text-xs font-bold text-slate-600">{res.id}</span>
                  <span className="text-xs text-slate-400">• {res.project}</span>
                  <span className="text-xs text-slate-400">• By {res.authorOrCreator}</span>
                </div>

                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-xl border border-emerald-200">
                  {res.relevanceScore}% RAG Match
                </span>
              </div>

              <div>
                <h3 className="font-bold text-slate-900 text-base group-hover:text-blue-600 transition-colors flex items-center gap-2">
                  <span>{res.title}</span>
                  <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-1">{res.snippet}</p>
              </div>

              {/* Tags list */}
              <div className="flex items-center gap-1.5 pt-1">
                {res.tags.map((tag, idx) => (
                  <span key={idx} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono font-medium">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          ))
        ) : (
          /* Empty Search State */
          <div className="bg-white rounded-2xl p-12 border border-slate-200 shadow-sm text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-800">No matching search results found</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No notebook entries, samples, or sequences matched <strong className="text-slate-800">"{query}"</strong> under category filter <strong className="text-slate-800">"{selectedFilter}"</strong>.
            </p>
            <button
              onClick={() => { setQuery(''); setSelectedFilter('All'); }}
              className="mt-2 text-xs font-bold text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
            >
              Clear filters and search query
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

