import { apiClient } from './apiClient';
import { DashboardResponse } from '../types/dashboard';

export const dashboardService = {
  getDashboardData: async (): Promise<DashboardResponse> => {
    const response = await apiClient.get<DashboardResponse>('/dashboard/');
    return response.data;
  }
};
