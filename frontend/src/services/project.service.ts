import { apiClient } from './apiClient';
import { 
  ProjectListResponse, ProjectDetail, ProjectCreate, ProjectUpdate, Project
} from '../types/project';

export const projectService = {
  getProjects: async (
    page = 1, 
    pageSize = 20, 
    search?: string, 
    status?: string, 
    priority?: string
  ): Promise<ProjectListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);

    const response = await apiClient.get<ProjectListResponse>(`/projects?${params.toString()}`);
    return response.data;
  },

  getProject: async (id: string): Promise<ProjectDetail> => {
    const response = await apiClient.get<ProjectDetail>(`/projects/${id}`);
    return response.data;
  },

  createProject: async (data: ProjectCreate): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', data);
    return response.data;
  },

  updateProject: async (id: string, data: ProjectUpdate): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data);
    return response.data;
  },

  deleteProject: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },

  archiveProject: async (id: string, reason?: string): Promise<Project> => {
    const response = await apiClient.post<Project>(`/projects/${id}/archive`, { archive_reason: reason });
    return response.data;
  },
  
  unarchiveProject: async (id: string): Promise<Project> => {
    const response = await apiClient.post<Project>(`/projects/${id}/restore`);
    return response.data;
  },

  addCollaborator: async (projectId: string, userId: string, role: string): Promise<any> => {
    const response = await apiClient.post(`/projects/${projectId}/collaborators`, {
      user_id: userId,
      role: role
    });
    return response.data;
  }
};
