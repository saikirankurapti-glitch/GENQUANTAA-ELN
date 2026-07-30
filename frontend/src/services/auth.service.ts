import { apiClient } from './apiClient';
import { LoginRequest, TokenResponse, User } from '../types/auth';

export const authService = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  register: async (data: any): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  updateProfile: async (data: { department?: string; designation?: string }): Promise<any> => {
    const response = await apiClient.put('/profiles/me', data);
    return response.data;
  },
  
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  }
};
