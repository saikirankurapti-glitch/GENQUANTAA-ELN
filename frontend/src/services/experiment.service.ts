import { apiClient } from './apiClient';
import { 
  ExperimentListResponse, ExperimentDetail, ExperimentCreate, ExperimentUpdate, Experiment
} from '../types/experiment';

export const experimentService = {
  getExperiments: async (
    page = 1, 
    pageSize = 20, 
    projectId?: string,
    search?: string, 
    status?: string, 
    priority?: string
  ): Promise<ExperimentListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (projectId) params.append('project_id', projectId);
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);

    const response = await apiClient.get<ExperimentListResponse>(`/experiments?${params.toString()}`);
    return response.data;
  },

  getExperiment: async (id: string): Promise<ExperimentDetail> => {
    const response = await apiClient.get<ExperimentDetail>(`/experiments/${id}`);
    return response.data;
  },

  createExperiment: async (data: ExperimentCreate): Promise<Experiment> => {
    const response = await apiClient.post<Experiment>('/experiments', data);
    return response.data;
  },

  updateExperiment: async (id: string, data: ExperimentUpdate): Promise<Experiment> => {
    const response = await apiClient.put<Experiment>(`/experiments/${id}`, data);
    return response.data;
  },

  deleteExperiment: async (id: string): Promise<void> => {
    await apiClient.delete(`/experiments/${id}`);
  },

  archiveExperiment: async (id: string, reason?: string): Promise<Experiment> => {
    const response = await apiClient.post<Experiment>(`/experiments/${id}/archive`, { archive_reason: reason });
    return response.data;
  },
  
  unarchiveExperiment: async (id: string): Promise<Experiment> => {
    const response = await apiClient.post<Experiment>(`/experiments/${id}/restore`);
    return response.data;
  },

  getQAComments: async (experimentId: string) => {
    const response = await apiClient.get<any[]>(`/experiments/${experimentId}/comments`);
    return response.data;
  },

  addQAComment: async (experimentId: string, data: { section_id: string; section_title?: string; target_text?: string; comment: string; category?: string }) => {
    const response = await apiClient.post<any>(`/experiments/${experimentId}/comments`, data);
    return response.data;
  },

  replyQAComment: async (experimentId: string, commentId: string, comment: string) => {
    const response = await apiClient.post<any>(`/experiments/${experimentId}/comments/${commentId}/reply`, { comment });
    return response.data;
  },

  resolveQAComment: async (experimentId: string, commentId: string, status: 'resolved' | 'open', resolutionNote?: string) => {
    const response = await apiClient.patch<any>(`/experiments/${experimentId}/comments/${commentId}/resolve`, {
      status,
      resolution_note: resolutionNote
    });
    return response.data;
  }
};
