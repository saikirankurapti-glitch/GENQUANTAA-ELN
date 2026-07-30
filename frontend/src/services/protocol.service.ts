import { apiClient } from './apiClient';
import { 
  ProtocolListResponse, ProtocolDetail, ProtocolCreate, ProtocolUpdate, Protocol, ProtocolApprovalCreate
} from '../types/protocol';

export const protocolService = {
  getProtocols: async (
    page = 1, 
    pageSize = 20, 
    category?: string,
    status?: string,
    ownerId?: string,
    search?: string
  ): Promise<ProtocolListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (category) params.append('category', category);
    if (status) params.append('status', status);
    if (ownerId) params.append('owner_id', ownerId);
    if (search) params.append('search', search);

    const response = await apiClient.get<ProtocolListResponse>(`/protocols?${params.toString()}`);
    return response.data;
  },

  getProtocol: async (id: string): Promise<ProtocolDetail> => {
    const response = await apiClient.get<ProtocolDetail>(`/protocols/${id}`);
    return response.data;
  },

  createProtocol: async (data: ProtocolCreate): Promise<Protocol> => {
    const response = await apiClient.post<Protocol>('/protocols', data);
    return response.data;
  },

  updateProtocol: async (id: string, data: ProtocolUpdate): Promise<Protocol> => {
    const response = await apiClient.put<Protocol>(`/protocols/${id}`, data);
    return response.data;
  },

  deleteProtocol: async (id: string): Promise<void> => {
    await apiClient.delete(`/protocols/${id}`);
  },

  approveProtocol: async (id: string, data: ProtocolApprovalCreate): Promise<any> => {
    const response = await apiClient.post(`/protocols/${id}/approve`, data);
    return response.data;
  }
};
