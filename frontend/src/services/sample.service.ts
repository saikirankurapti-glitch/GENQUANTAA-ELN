import { apiClient } from './apiClient';
import { 
  SampleListResponse, SampleDetail, SampleCreate, SampleUpdate, Sample
} from '../types/sample';

export const sampleService = {
  getSamples: async (
    page = 1, 
    pageSize = 20, 
    experimentId?: string,
    status?: string, 
    search?: string
  ): Promise<SampleListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (experimentId) params.append('experiment_id', experimentId);
    if (status) params.append('status', status);
    if (search) params.append('search', search);

    const response = await apiClient.get<SampleListResponse>(`/samples?${params.toString()}`);
    return response.data;
  },

  getSample: async (id: string): Promise<SampleDetail> => {
    const response = await apiClient.get<SampleDetail>(`/samples/${id}`);
    return response.data;
  },

  createSample: async (data: SampleCreate): Promise<Sample> => {
    const response = await apiClient.post<Sample>('/samples', data);
    return response.data;
  },

  updateSample: async (id: string, data: SampleUpdate): Promise<Sample> => {
    const response = await apiClient.put<Sample>(`/samples/${id}`, data);
    return response.data;
  },

  deleteSample: async (id: string): Promise<void> => {
    await apiClient.delete(`/samples/${id}`);
  },

  archiveSample: async (id: string): Promise<Sample> => {
    const response = await apiClient.post<Sample>(`/samples/${id}/archive`);
    return response.data;
  }
};
