import { apiClient } from './apiClient';
import { 
  NotebookListResponse, NotebookEntryDetail, NotebookEntryCreate, NotebookEntryUpdate, NotebookEntry
} from '../types/notebook';

export const notebookService = {
  getNotebookEntries: async (
    page = 1, 
    pageSize = 20, 
    experimentId?: string,
    entryType?: string,
    search?: string
  ): Promise<NotebookListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (experimentId) params.append('experiment_id', experimentId);
    if (entryType) params.append('entry_type', entryType);
    if (search) params.append('search', search);

    const response = await apiClient.get<NotebookListResponse>(`/notebook?${params.toString()}`);
    return response.data;
  },

  getNotebookEntry: async (id: string): Promise<NotebookEntryDetail> => {
    const response = await apiClient.get<NotebookEntryDetail>(`/notebook/${id}`);
    return response.data;
  },

  createNotebookEntry: async (data: NotebookEntryCreate): Promise<NotebookEntry> => {
    const response = await apiClient.post<NotebookEntry>('/notebook', data);
    return response.data;
  },

  updateNotebookEntry: async (id: string, data: NotebookEntryUpdate): Promise<NotebookEntry> => {
    const response = await apiClient.put<NotebookEntry>(`/notebook/${id}`, data);
    return response.data;
  },

  deleteNotebookEntry: async (id: string): Promise<void> => {
    await apiClient.delete(`/notebook/${id}`);
  }
};
