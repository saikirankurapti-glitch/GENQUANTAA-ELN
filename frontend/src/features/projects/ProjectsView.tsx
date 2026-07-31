import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { FolderKanban, Plus, Search, Users, FlaskConical, ChevronRight, Loader2, AlertCircle } from 'lucide-react';
import { useProjects, useCreateProject } from '../../hooks/useProjects';
import { useAuth } from '../../providers/AuthProvider';

interface ProjectsViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenProject?: (projectId: string) => void;
}

export const ProjectsView: React.FC<ProjectsViewProps> = ({ onSelectView, onOpenProject }) => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>(''); // '' means All
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const { data: projectsData, isLoading, error } = useProjects(
    page, 
    pageSize, 
    searchQuery, 
    selectedStatus ? selectedStatus.toUpperCase() : undefined
  );
  const createProject = useCreateProject();

  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newTags, setNewTags] = useState('');
  const [newCode, setNewCode] = useState(`PRJ-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`);

  const statuses = [{ label: 'All', value: '' }, { label: 'Planned', value: 'PLANNED' }, { label: 'Active', value: 'ACTIVE' }, { label: 'Completed', value: 'COMPLETED' }, { label: 'On Hold', value: 'ON_HOLD' }];

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      await createProject.mutateAsync({
        project_code: newCode,
        name: newTitle,
        description: newDesc,
        status: 'active',
        tags: newTags ? newTags.split(',').map(t => t.trim()) : ['New Project'],
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        visibility: 'PRIVATE'
      });
      setNewTitle('');
      setNewDesc('');
      setNewTags('');
      setNewCode(`PRJ-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`);
      setShowModal(false);
    } catch (err) {
      console.error("Failed to create project:", err);
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
              placeholder="Search projects by title, description, or tags..."
              className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs font-semibold text-slate-400 mr-1">Status:</span>
          {statuses.map((st) => (
            <button
              key={st.value}
              onClick={() => setSelectedStatus(st.value)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                selectedStatus === st.value
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st.label}
            </button>
          ))}
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors ml-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
           <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : error ? (
        <div className="flex justify-center p-12 text-rose-500">
           <AlertCircle className="w-6 h-6 mr-2" /> Failed to load projects.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
            {projectsData?.items.map((project) => (
              <div
                key={project.id}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                        <FolderKanban className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                          {project.project_code}
                        </span>
                        <h3 className="font-bold text-slate-800 text-base mt-1">{project.name}</h3>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      project.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-700' :
                      project.status === 'ON_HOLD' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {project.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-3">{project.description}</p>

                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {project.tags.map((tag, idx) => (
                      <span key={idx} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <FlaskConical className="w-3.5 h-3.5 text-blue-500" />
                      Experiments
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-slate-400" />
                      Members
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      if (onOpenProject) {
                        onOpenProject(project.id);
                      } else {
                        onSelectView('eln');
                      }
                    }}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 group cursor-pointer"
                  >
                    <span>Open Space</span>
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {projectsData?.items.length === 0 && (
             <div className="p-12 text-center text-slate-500">
               No projects found matching your criteria.
             </div>
          )}

          {/* Pagination Controls */}
          {projectsData && projectsData.total_pages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-6">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 rounded-lg disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-xs text-slate-600 font-semibold">Page {page} of {projectsData.total_pages}</span>
              <button 
                disabled={page >= projectsData.total_pages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 rounded-lg disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">Create New Research Workspace</h3>
            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Project Code</label>
                <input
                  type="text"
                  required
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500 font-mono text-slate-500 bg-slate-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. CRISPR Knockout Target Identification"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Summarize project goals, protocols, and hypothesis..."
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
                ></textarea>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tags (comma separated)</label>
                <input
                  type="text"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  placeholder="e.g. CRISPR, Cas9, HEK293T"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createProject.isPending}
                  className="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm cursor-pointer disabled:opacity-50"
                >
                  {createProject.isPending ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
