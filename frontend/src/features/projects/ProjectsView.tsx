import React, { useState } from 'react';
import type { ViewMode } from '../../types';
import { FolderKanban, Plus, Search, Users, FlaskConical, ChevronRight, Loader2, AlertCircle, Lock, Calendar, Clock, AlertTriangle } from 'lucide-react';
import { useProjects, useCreateProject } from '../../hooks/useProjects';
import { useUsers } from '../../hooks/useUsers';
import { projectService } from '../../services/project.service';
import { useAuth } from '../../providers/AuthProvider';
import { canCreateProjects, isUserAdmin } from '../../utils/permissions';

interface ProjectsViewProps {
  onSelectView: (view: ViewMode) => void;
  onOpenProject?: (projectId: string) => void;
}

export const ProjectsView: React.FC<ProjectsViewProps> = ({ onSelectView, onOpenProject }) => {
  const { user } = useAuth();
  const canCreate = canCreateProjects(user);
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
  const [newTargetEndDate, setNewTargetEndDate] = useState('');

  const statuses = [{ label: 'All', value: '' }, { label: 'Planned', value: 'PLANNED' }, { label: 'Active', value: 'ACTIVE' }, { label: 'Completed', value: 'COMPLETED' }, { label: 'On Hold', value: 'ON_HOLD' }];

  const getDeadlineInfo = (targetDate?: string | null, status?: string) => {
    if (status === 'COMPLETED') return { label: 'Completed', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: '✓' };
    if (!targetDate) return null;
    const diffDays = Math.ceil((new Date(targetDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { label: `${Math.abs(diffDays)}d Overdue`, color: 'bg-rose-50 text-rose-700 border-rose-200 font-bold', icon: '⚠' };
    if (diffDays === 0) return { label: 'Due Today', color: 'bg-amber-50 text-amber-700 border-amber-200 font-bold', icon: '⏰' };
    if (diffDays <= 7) return { label: `${diffDays}d left`, color: 'bg-amber-50 text-amber-700 border-amber-200', icon: '⏰' };
    return { label: `Due ${new Date(targetDate).toLocaleDateString()}`, color: 'bg-blue-50 text-blue-700 border-blue-200', icon: '📅' };
  };

  // Team Member Assignment State
  const [selectedMembers, setSelectedMembers] = useState<{id: string, name: string, role: string, email: string}[]>([]);
  const [userSearch, setUserSearch] = useState('');
  const { data: usersData, isLoading: usersLoading } = useUsers(1, 50, userSearch);

  const toggleMember = (u: any, role: string = 'Researcher') => {
    if (selectedMembers.find(m => m.id === u.id)) {
      setSelectedMembers(selectedMembers.filter(m => m.id !== u.id));
    } else {
      setSelectedMembers([...selectedMembers, { id: u.id, name: `${u.first_name} ${u.last_name}`, email: u.email, role }]);
    }
  };

  const updateMemberRole = (id: string, newRole: string) => {
    setSelectedMembers(selectedMembers.map(m => m.id === id ? { ...m, role: newRole } : m));
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      const newProject = await createProject.mutateAsync({
        project_code: newCode,
        name: newTitle,
        description: newDesc,
        status: 'active',
        tags: newTags ? newTags.split(',').map(t => t.trim()) : ['New Project'],
        organization_id: user?.organization_id || user?.tenant_id || '00000000-0000-0000-0000-000000000000',
        visibility: 'PRIVATE',
        target_end_date: newTargetEndDate || undefined
      });
      
      // Add team members
      for (const member of selectedMembers) {
        try {
          await projectService.addCollaborator(newProject.id, member.id, member.role);
        } catch (collabErr) {
          console.error("Failed to add collaborator", collabErr);
        }
      }

      setNewTitle('');
      setNewDesc('');
      setNewTags('');
      setNewTargetEndDate('');
      setNewCode(`PRJ-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`);
      setSelectedMembers([]);
      setUserSearch('');
      setShowModal(false);
      
      // Auto-navigate to the new project to view the team
      if (onOpenProject && newProject?.id) {
        onOpenProject(newProject.id);
      }
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
          {/* Only Admin / PI can create projects */}
          {canCreate && (
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors ml-2 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>New Project</span>
            </button>
          )}
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
                    <div className="flex items-center gap-1.5 flex-wrap justify-end">
                      {(() => {
                        const dl = getDeadlineInfo(project.target_end_date, project.status);
                        return dl ? (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border flex items-center gap-1 ${dl.color}`}>
                            <span>{dl.icon}</span>
                            <span>{dl.label}</span>
                          </span>
                        ) : null;
                      })()}
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        project.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-700' :
                        project.status === 'ON_HOLD' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {project.status}
                      </span>
                    </div>
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
            <div className="col-span-full">
              {canCreate ? (
                <div className="p-12 text-center text-slate-500">
                  No projects found matching your criteria.
                </div>
              ) : (
                <div className="p-12 text-center flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center">
                    <Lock className="w-8 h-8 text-blue-400" />
                  </div>
                  <h3 className="font-bold text-slate-700 text-base">No projects assigned yet</h3>
                  <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                    You will see projects here once a <strong>PI or Admin</strong> adds you as a collaborator.
                    Contact your Principal Investigator to be added to an active project.
                  </p>
                </div>
              )}
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

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-blue-600" /> Target Completion Deadline (Admin / PI)
                </label>
                <input
                  type="date"
                  value={newTargetEndDate}
                  onChange={(e) => setNewTargetEndDate(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="pt-2 border-t border-slate-100">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assign Team Members (Optional)</label>
                
                {/* Selected Members Display */}
                {selectedMembers.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {selectedMembers.map(m => (
                      <div key={m.id} className="flex items-center gap-1 bg-blue-50 border border-blue-100 text-blue-700 px-2 py-1 rounded text-[10px] font-semibold">
                        <span>{m.name}</span>
                        <select 
                          value={m.role}
                          onChange={(e) => updateMemberRole(m.id, e.target.value)}
                          className="bg-transparent border-none outline-none font-bold text-blue-800 cursor-pointer ml-1 text-[10px]"
                        >
                          <option value="Researcher">Researcher</option>
                          <option value="Bioinformatician">Bioinformatician</option>
                          <option value="QA">QA</option>
                          <option value="Viewer">Viewer</option>
                        </select>
                        <button type="button" onClick={() => toggleMember({id: m.id})} className="hover:text-blue-900 ml-1 font-bold text-sm leading-none">&times;</button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    placeholder="Search users to add..."
                    className="w-full border border-slate-200 rounded-lg py-2 pl-8 pr-2 text-xs focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* User Search Results */}
                <div className="mt-1 border border-slate-200 rounded-lg max-h-32 overflow-y-auto bg-slate-50 p-1 space-y-1">
                  {usersLoading ? (
                    <div className="flex justify-center p-2"><Loader2 className="w-3 h-3 animate-spin text-slate-400" /></div>
                  ) : (() => {
                    const availableUsers = usersData?.items?.filter((u: any) => !isUserAdmin(u) && u.id !== user?.id) || [];
                    if (availableUsers.length === 0) {
                      return <div className="text-[10px] text-slate-500 p-1 text-center">No available users found</div>;
                    }
                    return availableUsers.map((u: any) => {
                      const isSelected = selectedMembers.some(m => m.id === u.id);
                      return (
                        <div 
                          key={u.id}
                          className={`p-1.5 rounded flex items-center justify-between ${isSelected ? 'bg-blue-100' : 'hover:bg-white cursor-pointer border border-transparent hover:border-slate-200'}`}
                          onClick={() => !isSelected && toggleMember(u)}
                        >
                          <div className="flex flex-col">
                            <span className="text-[11px] font-bold text-slate-800">{u.first_name} {u.last_name}</span>
                            <span className="text-[9px] text-slate-500">{u.email}</span>
                          </div>
                          {isSelected ? (
                            <span className="text-[9px] font-bold text-blue-600 bg-white px-1.5 py-0.5 rounded border border-blue-200">Added</span>
                          ) : (
                            <span className="text-[9px] font-bold text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200 hover:text-blue-600">Add</span>
                          )}
                        </div>
                      );
                    })
                  })()}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
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
