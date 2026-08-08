import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationService } from '../services/notification.service';
import { useAuth } from '../providers/AuthProvider';

export const useNotifications = (limit: number = 50, unreadOnly: boolean = false) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ['notifications', limit, unreadOnly],
    queryFn: () => notificationService.getNotifications(limit, unreadOnly),
    enabled: isAuthenticated,
    refetchInterval: 10000, // Poll every 10 seconds for real-time updates
    staleTime: 5000,
  });
};

export const useUnreadNotificationCount = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ['notifications_unread_count'],
    queryFn: () => notificationService.getUnreadCount(),
    enabled: isAuthenticated,
    refetchInterval: 10000, // Poll every 10 seconds
    staleTime: 5000,
  });
};

export const useMarkNotificationAsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => notificationService.markAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications_unread_count'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useMarkAllNotificationsAsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications_unread_count'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};
