import React, { useState, useMemo } from 'react';
import { ViewMode } from '../../types';
import { FlaskConical, Loader2, Search, Plus, Filter, Tag, Calendar, Sparkles, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { useExperiments, useCreateExperiment } from '../../hooks/useExperiments';
import { useAuth } from '../../providers/AuthProvider';
import { canCreateExperiment } from '../../utils/permissions';

interface ExperimentsListViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
}

const DEFAULT_SAMPLE_EXPERIMENTS = [
  {
    id: 'EXP-2024-101',
    experiment_code: 'EXP-2024-101',
    title: 'CRISPR-Cas9 sgRNA Knockout Efficiency Screening (VEGFR2)',
    objective: 'Screening 6 candidate sgRNAs targeting exon 3 of human VEGFR2 locus in HEK293T cells.',
    description: 'Systematic validation of CRISPR-Cas9 editing efficiency on the VEGFR2 locus in HEK293T cells.',
    status: 'in_progress',
    priority: 'HIGH',
    updated_at: new Date().toISOString(),
    tags: ['CRISPR', 'Oncology', 'VEGFR2', 'T7E1']
  },
  {
    id: 'EXP-002',
    experiment_code: 'EXP-002',
    title: 'LNP Formulation Optimisation – mRNA Encapsulation Efficiency',
    objective: 'Optimise lipid nanoparticle (LNP) N/P ratio for maximum mRNA encapsulation efficiency.',
    description: 'Five LNP formulations with varying N/P ratios prepared and evaluated via RiboGreen assay.',
    status: 'completed',
    priority: 'HIGH',
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    tags: ['mRNA', 'LNP', 'Formulation', 'Nanoparticles']
  },
  {
    id: 'EXP-003',
    experiment_code: 'EXP-003',
    title: '16S rRNA V3-V4 Amplicon Sequencing – Cohort Batch 1',
    objective: 'Generate 16S amplicon sequencing data for first 40 subjects from the dietary intervention cohort.',
    description: 'Microbial community profiling from genomic DNA extracted from stool samples.',
    status: 'in_progress',
    priority: 'MEDIUM',
    updated_at: new Date(Date.now() - 172800000).toISOString(),
    tags: ['Microbiome', '16S rRNA', 'NGS', 'Bioinformatics']
  },
  {
    id: 'EXP-2024-102',
    experiment_code: 'EXP-2024-102',
    title: 'mRNA-1273 Stability Assessment at 4°C vs -20°C',
    objective: 'Longitudinal stability study of formulated mRNA batches over 30 days under varied thermal conditions.',
    description: 'Assessing capillary electrophoresis purity and translational potency post thermal challenge.',
    status: 'completed',
    priority: 'MEDIUM',
    updated_at: new Date(Date.now() - 345600000).toISOString(),
    tags: ['Stability', 'mRNA', 'Quality Control']
  },
  {
    id: 'EXP-2024-103',
    experiment_code: 'EXP-2024-103',
    title: 'Automated Liquid Handler Calibration & Accuracy Run',
    objective: 'Routine gravimetric and photometric calibration of Tecan Freedom EVO 150.',
    description: 'Verification of 8-channel pipetting arm across 1µL to 200µL dynamic volume range.',
    status: 'draft',
    priority: 'LOW',
    updated_at: new Date(Date.now() - 518400000).toISOString(),
    tags: ['Calibration', 'Robotics', 'Maintenance']
  }
];

export const ExperimentsListView: React.FC<ExperimentsListViewProps> = ({ 
  onSelectView, 
  onOpenExperiment 
}) => {
  const { user } = useAuth();
  const canCreateExp = canCreateExperiment(user);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'in_progress' | 'completed' | 'draft'>('all');
  
  const pageSize = 12;

  const { data: experimentsData, isLoading } = useExperiments(
    page, 
    pageSize, 
    undefined, 
    search || undefined
  );

  const createExperiment = useCreateExperiment();

  // Combine API items with fallback demo items if API returns empty list
  const displayItems = useMemo(() => {
    let items = (experimentsData?.items && experimentsData.items.length > 0)
      ? experimentsData.items
      : DEFAULT_SAMPLE_EXPERIMENTS;

    if (search.trim()) {
      const q = search.toLowerCase();
      items = items.filter((item: any) => 
        (item.title || '').toLowerCase().includes(q) ||
        (item.experiment_code || '').toLowerCase().includes(q) ||
        (item.objective || '').toLowerCase().includes(q)
      );
    }

    if (statusFilter !== 'all') {
      items = items.filter((item: any) => (item.status || '').toLowerCase() === statusFilter);
    }

    return items;
  }, [experimentsData, search, statusFilter]);

  const handleCreateExperiment = async () => {
    try {
      const newExp = await createExperiment.mutateAsync({
        title: 'New Experiment Entry',
        experiment_code: `EXP-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        status: 'draft',
        priority: 'MEDIUM',
        tenant_id: user?.tenant_id || '00000000-0000-0000-0000-000000000000'
      });
      onOpenExperiment((newExp as any).id || (newExp as any).experiment_code);
    } catch (e) {
      console.error("Failed to create experiment", e);
      // Fallback: open ELN Editor with new experiment code
      const fallbackCode = `EXP-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;
      onOpenExperiment(fallbackCode);
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'completed') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (status === 'in_progress') return 'bg-blue-50 text-blue-700 border-blue-200';
    return 'bg-amber-50 text-amber-700 border-amber-200';
  };

  const getDeadlineBadge = (plannedEndDate?: string | null, status?: string) => {
    if (status === 'completed') return null;
    if (!plannedEndDate) return null;
    const diffDays = Math.ceil((new Date(plannedEndDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { label: `${Math.abs(diffDays)}d Overdue`, color: 'bg-rose-50 text-rose-700 border-rose-200 font-bold', icon: '⚠' };
    if (diffDays === 0) return { label: 'Due Today', color: 'bg-amber-50 text-amber-700 border-amber-200 font-bold', icon: '⏰' };
    if (diffDays <= 7) return { label: `${diffDays}d left`, color: 'bg-amber-50 text-amber-700 border-amber-200', icon: '⏰' };
    return { label: `Due ${new Date(plannedEndDate).toLocaleDateString()}`, color: 'bg-blue-50 text-blue-700 border-blue-200', icon: '📅' };
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-800">All Experiments</h1>
            <span className="bg-blue-50 text-blue-700 text-xs font-bold px-2.5 py-0.5 rounded-full border border-blue-200">
              {displayItems.length} {displayItems.length === 1 ? 'Entry' : 'Entries'}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Browse and manage all your ELN experiments across research projects.
          </p>
        </div>
        {canCreateExp && (
          <button
            onClick={handleCreateExperiment}
            disabled={createExperiment.isPending}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {createExperiment.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            New Experiment
          </button>
        )}
      </div>

      {/* Filters and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search experiments by title or code..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {(['all', 'in_progress', 'completed', 'draft'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                statusFilter === tab
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab === 'all' ? 'All Status' : tab === 'in_progress' ? 'In Progress' : tab === 'completed' ? 'Completed' : 'Draft'}
            </button>
          ))}
        </div>
      </div>

      {/* Content Grid */}
      {isLoading && (!experimentsData?.items || experimentsData.items.length === 0) ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : displayItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-500 bg-white rounded-2xl border border-dashed border-slate-200">
          <FlaskConical className="w-12 h-12 text-slate-300 mb-4" />
          <p className="text-base font-semibold text-slate-700">No matching experiments found</p>
          <p className="text-sm mt-1 mb-4">Try clearing your filters or search keywords.</p>
          <button 
            onClick={() => { setSearch(''); setStatusFilter('all'); }}
            className="text-blue-600 font-semibold text-sm hover:underline cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {displayItems.map((exp: any) => (
            <div 
              key={exp.id || exp.experiment_code}
              onClick={() => onOpenExperiment(exp.id || exp.experiment_code)}
              className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-400 hover:shadow-lg hover:shadow-blue-500/5 transition-all cursor-pointer group flex flex-col justify-between h-full"
            >
              <div>
                <div className="flex justify-between items-start mb-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white text-blue-600 transition-colors shrink-0">
                    <FlaskConical className="w-5 h-5" />
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap justify-end">
                    {(() => {
                      const dl = getDeadlineBadge(exp.planned_end_date, exp.status);
                      return dl ? (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border flex items-center gap-1 ${dl.color}`}>
                          <span>{dl.icon}</span>
                          <span>{dl.label}</span>
                        </span>
                      ) : null;
                    })()}
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${getStatusBadge(exp.status)}`}>
                      {(exp.status || 'draft').toUpperCase().replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1 block">
                  {exp.experiment_code || exp.id}
                </span>
                <h3 className="font-bold text-slate-800 text-base mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                  {exp.title}
                </h3>
                <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                  {exp.objective || exp.description || 'Systematic experimental notebook run with recorded telemetry.'}
                </p>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-[11px] font-medium text-slate-500">
                <span className="flex items-center gap-1 text-slate-400">
                  <Clock className="w-3.5 h-3.5" />
                  {exp.updated_at ? new Date(exp.updated_at).toLocaleDateString() : 'Recent'}
                </span>
                <span className="group-hover:text-blue-600 text-blue-600 font-semibold transition-colors flex items-center gap-1">
                  Open Notebook
                  <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
