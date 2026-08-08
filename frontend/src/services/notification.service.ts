import { apiClient } from './apiClient';
import type { NotificationItem } from '../types';

export const notificationService = {
  async getNotifications(limit: number = 50, unreadOnly: boolean = false): Promise<NotificationItem[]> {
    const res = await apiClient.get<NotificationItem[]>('/notifications', {
      params: { limit, unread_only: unreadOnly }
    });
    return res.data;
  },

  async getUnreadCount(): Promise<number> {
    const res = await apiClient.get<{ unread_count: number }>('/notifications/unread-count');
    return res.data.unread_count;
  },

  async markAsRead(notificationId: string): Promise<void> {
    await apiClient.patch(`/notifications/${notificationId}/read`);
  },

  async markAllAsRead(): Promise<void> {
    await apiClient.post('/notifications/mark-all-read');
  }
};
