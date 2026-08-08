import { apiClient } from './apiClient';
import { User } from '../types/auth';

export const userService = {
  getUsers: async (
    page = 1, 
    pageSize = 20, 
    search?: string
  ): Promise<{ items: User[], total: number, page: number, size: number, pages: number }> => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: pageSize.toString(),
    });
    
    if (search) params.append('search', search);

    const response = await apiClient.get(`/users?${params.toString()}`);
    return response.data;
  }
};
