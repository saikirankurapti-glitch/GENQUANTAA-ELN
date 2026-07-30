import { apiClient } from './apiClient';
import { 
  SequenceListResponse, SequenceDetail, SequenceCreate, SequenceUpdate, SequenceRead
} from '../types/sequence';

export const sequenceService = {
  getSequences: async (
    page = 1, 
    pageSize = 20, 
    sequenceType?: string,
    status?: string,
    experimentId?: string,
    sampleId?: string,
    search?: string
  ): Promise<SequenceListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (sequenceType) params.append('sequence_type', sequenceType);
    if (status) params.append('status', status);
    if (experimentId) params.append('experiment_id', experimentId);
    if (sampleId) params.append('sample_id', sampleId);
    if (search) params.append('search', search);

    const response = await apiClient.get<SequenceListResponse>(`/sequences?${params.toString()}`);
    return response.data;
  },

  getSequence: async (id: string): Promise<SequenceDetail> => {
    const response = await apiClient.get<SequenceDetail>(`/sequences/${id}`);
    return response.data;
  },

  createSequence: async (data: SequenceCreate): Promise<SequenceRead> => {
    const response = await apiClient.post<SequenceRead>('/sequences', data);
    return response.data;
  },

  updateSequence: async (id: string, data: SequenceUpdate): Promise<SequenceRead> => {
    const response = await apiClient.put<SequenceRead>(`/sequences/${id}`, data);
    return response.data;
  },

  deleteSequence: async (id: string): Promise<void> => {
    await apiClient.delete(`/sequences/${id}`);
  }
};
