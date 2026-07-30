import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboard.service';
import { useAuth } from '../providers/AuthProvider';

export const useDashboard = () => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardService.getDashboardData,
    enabled: isAuthenticated,
  });
};
