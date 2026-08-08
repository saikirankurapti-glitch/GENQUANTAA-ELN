import React, { useState } from 'react';
import { ViewMode } from '../../types';
import { ArrowLeft, FlaskConical, FolderKanban, Loader2, AlertCircle, Plus, Calendar, Target, Tag, Users, UserPlus, X } from 'lucide-react';
import { useProject, useAddCollaborator, useUpdateProject } from '../../hooks/useProjects';
import { useExperiments, useCreateExperiment } from '../../hooks/useExperiments';
import { useUsers } from '../../hooks/useUsers';
import { useAuth } from '../../providers/AuthProvider';
import { canCreateExperiment, canManageTeam, isUserAdmin, normalizeRole } from '../../utils/permissions';

interface ProjectDetailViewProps {
  projectId: string;
  onSelectView: (view: ViewMode) => void;
  onOpenExperiment: (expId: string) => void;
}

export const ProjectDetailView: React.FC<ProjectDetailViewProps> = ({ 
  projectId, 
  onSelectView,
  onOpenExperiment
}) => {
  const { user } = useAuth();
  const canCreateExp = canCreateExperiment(user);
  const canManage = canManageTeam(user);
  const isDeadlineManager = isUserAdmin(user) || normalizeRole(user) === 'PI';
  const { data: project, isLoading: projectLoading, error: projectError } = useProject(projectId);
  const updateProject = useUpdateProject();

  const [isEditingDeadline, setIsEditingDeadline] = useState(false);
  const [targetDateVal, setTargetDateVal] = useState('');

  React.useEffect(() => {
    if (project?.target_end_date) {
      setTargetDateVal(new Date(project.target_end_date).toISOString().split('T')[0]);
    }
  }, [project?.target_end_date]);

  const handleSaveDeadline = async () => {
    if (!project) return;
    try {
      await updateProject.mutateAsync({
        id: project.id,
        data: { target_end_date: targetDateVal || null }
      });
      setIsEditingDeadline(false);
    } catch (err) {
      console.error("Failed to update deadline:", err);
    }
  };
  
  const [page, setPage] = useState(1);
  const pageSize = 10;
  
  const { data: experimentsData, isLoading: experimentsLoading } = useExperiments(
    page, 
    pageSize, 
    projectId
  );

  const createExperiment = useCreateExperiment();

  const handleCreateExperiment = async () => {
    try {
      const newExp = await createExperiment.mutateAsync({
        project_id: projectId,
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

  // Add Member Modal State
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState('Researcher');
  
  const { data: usersData, isLoading: usersLoading } = useUsers(1, 20, userSearch);
  const addCollaborator = useAddCollaborator();

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await addCollaborator.mutateAsync({
        projectId,
        userId: selectedUser,
        role: selectedRole
      });
      setShowMemberModal(false);
      setSelectedUser('');
      setUserSearch('');
    } catch (e) {
      console.error("Failed to add member", e);
    }
  };

  if (projectLoading) {
    return (
      <div className="flex justify-center p-12 h-full items-center">
         <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <div className="flex flex-col items-center justify-center p-12 h-full text-rose-500">
         <AlertCircle className="w-8 h-8 mb-4" />
         <span className="font-semibold">Failed to load project details.</span>
         <button onClick={() => onSelectView('projects')} className="mt-4 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 text-sm font-semibold">
           Back to Projects
         </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => onSelectView('projects')}
          className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
          <FolderKanban className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded uppercase tracking-wider">
              {project.project_code}
            </span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              project.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
              project.status === 'on_hold' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'
            }`}>
              {project.status.toUpperCase()}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mt-1">{project.name}</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Project Info */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2">Project Overview</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-1">Description</p>
                <p className="text-sm text-slate-700 leading-relaxed">{project.description || 'No description provided.'}</p>
              </div>

              {project.objective && (
                <div className="bg-blue-50/50 p-3 rounded-lg border border-blue-100/50">
                  <div className="flex items-center gap-1.5 text-blue-700 font-semibold text-xs mb-1">
                    <Target className="w-3.5 h-3.5" />
                    Objective
                  </div>
                  <p className="text-sm text-slate-700">{project.objective}</p>
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                {project.tags && project.tags.map((tag: string, idx: number) => (
                  <span key={idx} className="flex items-center gap-1 text-[11px] bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md font-medium">
                    <Tag className="w-3 h-3" />
                    {tag}
                  </span>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-100 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-slate-500 mb-1 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" /> Created
                  </p>
                  <p className="text-sm font-medium text-slate-800">
                    {new Date(project.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 mb-1">Priority</p>
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                    project.priority === 'CRITICAL' ? 'bg-rose-50 border-rose-200 text-rose-700' :
                    project.priority === 'HIGH' ? 'bg-orange-50 border-orange-200 text-orange-700' :
                    'bg-slate-50 border-slate-200 text-slate-700'
                  }`}>
                    {project.priority || 'MEDIUM'}
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-blue-600" /> Target Completion Deadline
                  </p>
                  {isDeadlineManager && (
                    <button 
                      onClick={() => setIsEditingDeadline(!isEditingDeadline)}
                      className="text-[10px] font-bold text-blue-600 hover:underline cursor-pointer"
                    >
                      {isEditingDeadline ? 'Cancel' : project.target_end_date ? 'Edit Deadline' : '+ Set Deadline'}
                    </button>
                  )}
                </div>

                {isEditingDeadline ? (
                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="date"
                      value={targetDateVal}
                      onChange={(e) => setTargetDateVal(e.target.value)}
                      className="border border-slate-200 rounded p-1.5 text-xs focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={handleSaveDeadline}
                      disabled={updateProject.isPending}
                      className="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                    >
                      {updateProject.isPending ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                ) : (
                  <div>
                    {project.target_end_date ? (
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-bold text-slate-800">
                          {new Date(project.target_end_date).toLocaleDateString()}
                        </p>
                        {(() => {
                          const diffDays = Math.ceil((new Date(project.target_end_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                          if (project.status === 'COMPLETED') return <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">Completed</span>;
                          if (diffDays < 0) return <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">⚠ {Math.abs(diffDays)}d Overdue</span>;
                          if (diffDays === 0) return <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">⏰ Due Today</span>;
                          if (diffDays <= 7) return <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">⏰ {diffDays}d left</span>;
                          return <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">{diffDays}d remaining</span>;
                        })()}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No deadline configured by Admin/PI.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Team Members Section */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-600" />
                Team Members
              </h3>
              {canManage && (
                <button 
                  onClick={() => setShowMemberModal(true)}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2 py-1 rounded transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  Add
                </button>
              )}
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <div>
                  <p className="text-xs font-bold text-slate-800">Owner</p>
                  <p className="text-[10px] text-slate-500">Project Creator</p>
                </div>
                <span className="text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded uppercase">Owner</span>
              </div>
              
              {project.collaborators && project.collaborators.length > 0 ? (
                project.collaborators.map((collab: any) => (
                  <div key={collab.user_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-100 transition-colors">
                    <div>
                      <p className="text-xs font-bold text-slate-800">{collab.user?.first_name} {collab.user?.last_name} {collab.user ? '' : collab.user_id}</p>
                      <p className="text-[10px] text-slate-500">{collab.user?.email || 'User'}</p>
                    </div>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded uppercase">{collab.role}</span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 text-center py-2">No additional members.</p>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Experiments List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full min-h-[500px]">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-800">Project Experiments</h3>
                <p className="text-xs text-slate-500">{experimentsData?.total || 0} total experiments</p>
              </div>
              {canCreateExp && (
                <button
                  onClick={handleCreateExperiment}
                  disabled={createExperiment.isPending}
                  className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-sm transition-colors cursor-pointer disabled:opacity-50"
                >
                  {createExperiment.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>New Experiment</span>
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {experimentsLoading ? (
                <div className="flex justify-center p-12">
                   <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                </div>
              ) : experimentsData?.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-slate-500 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                  <FlaskConical className="w-10 h-10 text-slate-300 mb-3" />
                  <p className="text-sm font-semibold text-slate-600">No experiments yet</p>
                  <p className="text-xs mt-1">Create an experiment to start documenting your research.</p>
                </div>
              ) : (
                experimentsData?.items.map((exp: any) => (
                  <div 
                    key={exp.id}
                    onClick={() => onOpenExperiment(exp.id)}
                    className="p-4 rounded-xl border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group bg-white"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                          {exp.experiment_code}
                        </span>
                        <h4 className="font-bold text-slate-800 text-sm group-hover:text-blue-600 transition-colors">
                          {exp.title}
                        </h4>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        exp.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                        exp.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {exp.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                      {exp.objective || exp.description || 'No description provided.'}
                    </p>
                    <div className="mt-3 flex justify-between items-center text-[10px] text-slate-400 font-semibold">
                      <span>Updated {new Date(exp.updated_at).toLocaleDateString()}</span>
                      <span className="group-hover:text-blue-500 transition-colors">Open &rarr;</span>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Pagination Controls */}
            {experimentsData && experimentsData.total_pages > 1 && (
              <div className="p-3 border-t border-slate-100 flex justify-center items-center gap-4 bg-slate-50 rounded-b-xl">
                <button 
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="px-2.5 py-1 text-xs font-semibold bg-white border border-slate-200 rounded text-slate-600 disabled:opacity-50"
                >
                  Prev
                </button>
                <span className="text-xs text-slate-500 font-medium">Page {page} of {experimentsData.total_pages}</span>
                <button 
                  disabled={page >= experimentsData.total_pages}
                  onClick={() => setPage(p => p + 1)}
                  className="px-2.5 py-1 text-xs font-semibold bg-white border border-slate-200 rounded text-slate-600 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Member Modal */}
      {showMemberModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-800">Add Team Member</h3>
              <button onClick={() => setShowMemberModal(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleAddMember} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Search User</label>
                <input
                  type="text"
                  placeholder="Type name or email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-indigo-500 mb-2"
                />
                
                <div className="border border-slate-200 rounded-lg max-h-40 overflow-y-auto bg-slate-50 p-1 space-y-1">
                  {usersLoading ? (
                    <div className="flex justify-center p-4"><Loader2 className="w-4 h-4 animate-spin text-slate-400" /></div>
                  ) : usersData?.items?.length === 0 ? (
                    <div className="text-xs text-slate-500 p-2 text-center">No users found</div>
                  ) : (
                    usersData?.items?.map(u => (
                      <div 
                        key={u.id}
                        onClick={() => setSelectedUser(u.id)}
                        className={`p-2 rounded cursor-pointer flex flex-col ${selectedUser === u.id ? 'bg-indigo-100 border border-indigo-200' : 'hover:bg-white border border-transparent'}`}
                      >
                        <span className="text-xs font-bold text-slate-800">{u.first_name} {u.last_name}</span>
                        <span className="text-[10px] text-slate-500">{u.email}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Project Role</label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  <option value="Researcher">Researcher</option>
                  <option value="Bioinformatician">Bioinformatician</option>
                  <option value="QA">QA</option>
                  <option value="Viewer">Viewer</option>
                  <option value="PI">Principal Investigator (PI)</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowMemberModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedUser || addCollaborator.isPending}
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm cursor-pointer disabled:opacity-50"
                >
                  {addCollaborator.isPending ? 'Adding...' : 'Add Member'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
