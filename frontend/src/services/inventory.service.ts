import { apiClient } from './apiClient';
import { 
  InventoryListResponse, InventoryItemDetail, InventoryItemCreate, InventoryItemUpdate, InventoryItem,
  InventoryReceiveRequest, InventoryIssueRequest
} from '../types/inventory';

export const inventoryService = {
  getInventory: async (
    page = 1, 
    pageSize = 20, 
    categoryId?: string,
    supplierId?: string,
    storageLocationId?: string,
    status?: string,
    isLowStock?: boolean,
    search?: string
  ): Promise<InventoryListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (categoryId) params.append('category_id', categoryId);
    if (supplierId) params.append('supplier_id', supplierId);
    if (storageLocationId) params.append('storage_location_id', storageLocationId);
    if (status) params.append('status', status);
    if (isLowStock !== undefined) params.append('is_low_stock', isLowStock.toString());
    if (search) params.append('search', search);

    const response = await apiClient.get<InventoryListResponse>(`/inventory?${params.toString()}`);
    return response.data;
  },

  getInventoryItem: async (id: string): Promise<InventoryItemDetail> => {
    const response = await apiClient.get<InventoryItemDetail>(`/inventory/${id}`);
    return response.data;
  },

  createInventoryItem: async (data: InventoryItemCreate): Promise<InventoryItem> => {
    const response = await apiClient.post<InventoryItem>('/inventory', data);
    return response.data;
  },

  updateInventoryItem: async (id: string, data: InventoryItemUpdate): Promise<InventoryItem> => {
    const response = await apiClient.put<InventoryItem>(`/inventory/${id}`, data);
    return response.data;
  },

  deleteInventoryItem: async (id: string): Promise<void> => {
    await apiClient.delete(`/inventory/${id}`);
  },

  receiveInventory: async (id: string, data: InventoryReceiveRequest): Promise<any> => {
    const response = await apiClient.post(`/inventory/${id}/receive`, data);
    return response.data;
  },

  issueInventory: async (id: string, data: InventoryIssueRequest): Promise<any> => {
    const response = await apiClient.post(`/inventory/${id}/issue`, data);
    return response.data;
  }
};
