import React, { useState } from 'react';
import { ViewMode } from '../../types';
import { FlaskConical, Loader2, Search, Plus, Filter } from 'lucide-react';
import { useExperiments, useCreateExperiment } from '../../hooks/useExperiments';
import { useAuth } from '../../providers/AuthProvider';

interface ExperimentsListViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
}

export const ExperimentsListView: React.FC<ExperimentsListViewProps> = ({ 
  onSelectView, 
  onOpenExperiment 
}) => {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  
  const pageSize = 12;

  const { data: experimentsData, isLoading } = useExperiments(
    page, 
    pageSize, 
    undefined, 
    search
  );

  const createExperiment = useCreateExperiment();

  const handleCreateExperiment = async () => {
    try {
      const newExp = await createExperiment.mutateAsync({
        title: 'New Experiment',
        experiment_code: `EXP-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        status: 'draft',
        priority: 'MEDIUM',
        tenant_id: user?.tenant_id || '00000000-0000-0000-0000-000000000000'
      });
      onOpenExperiment((newExp as any).id || (newExp as any).experiment_code);
    } catch (e) {
      console.error("Failed to create experiment", e);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">All Experiments</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse and manage all your ELN experiments across projects.
          </p>
        </div>
        <button
          onClick={handleCreateExperiment}
          disabled={createExperiment.isPending}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-sm transition-colors cursor-pointer disabled:opacity-50"
        >
          {createExperiment.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          New Experiment
        </button>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearch} className="relative w-full md:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search experiments by title or code..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </form>
        <div className="flex gap-2 w-full md:w-auto">
          <button className="flex items-center justify-center gap-2 px-4 py-2 border border-slate-200 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-50 w-full md:w-auto">
            <Filter className="w-4 h-4" />
            Filters
          </button>
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : experimentsData?.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-500 bg-white rounded-2xl border border-dashed border-slate-200">
          <FlaskConical className="w-12 h-12 text-slate-300 mb-4" />
          <p className="text-base font-semibold text-slate-700">No experiments found</p>
          <p className="text-sm mt-1 mb-4">Try adjusting your search criteria or create a new experiment.</p>
          <button 
            onClick={handleCreateExperiment}
            className="text-blue-600 font-semibold text-sm hover:underline"
          >
            Create New Experiment
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {experimentsData?.items.map((exp: any) => (
            <div 
              key={exp.id}
              onClick={() => onOpenExperiment(exp.id)}
              className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-400 hover:shadow-lg hover:shadow-blue-500/5 transition-all cursor-pointer group flex flex-col h-full"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white text-blue-600 transition-colors shrink-0">
                  <FlaskConical className="w-5 h-5" />
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  exp.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                  exp.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'
                }`}>
                  {exp.status.toUpperCase()}
                </span>
              </div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 block">
                {exp.experiment_code}
              </span>
              <h3 className="font-bold text-slate-800 text-base mb-2 group-hover:text-blue-600 transition-colors line-clamp-1">
                {exp.title}
              </h3>
              <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed flex-1">
                {exp.objective || exp.description || 'No description or objective provided.'}
              </p>
              
              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-[11px] font-medium text-slate-500">
                <span>{new Date(exp.updated_at).toLocaleDateString()}</span>
                <span className="group-hover:text-blue-600 transition-colors flex items-center gap-1">
                  Open 
                  <span className="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {experimentsData && experimentsData.total_pages > 1 && (
        <div className="flex justify-center items-center gap-4 py-4">
          <button 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="px-4 py-2 text-sm font-semibold bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 disabled:opacity-50 transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-slate-600 font-semibold">
            Page {page} of {experimentsData.total_pages}
          </span>
          <button 
            disabled={page >= experimentsData.total_pages}
            onClick={() => setPage(p => p + 1)}
            className="px-4 py-2 text-sm font-semibold bg-white border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-700 disabled:opacity-50 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
