import React from 'react';
import type { NotificationItem, ViewMode } from '../../types';
import { 
  MessageSquare, CheckCircle2, UserCheck, Sparkles, Check, 
  FolderKanban, FlaskConical, Bell, ArrowRight, Loader2, AlertCircle,
  Clock, ShieldCheck
} from 'lucide-react';
import { useNotifications, useMarkNotificationAsRead, useMarkAllNotificationsAsRead } from '../../hooks/useNotifications';

interface NotificationsViewProps {
  notifications?: NotificationItem[];
  onMarkAllAsRead?: () => void;
  onSelectView: (view: ViewMode) => void;
  onOpenProject?: (projectId: string) => void;
  onOpenExperiment?: (expId: string) => void;
}

export const NotificationsView: React.FC<NotificationsViewProps> = ({
  onSelectView,
  onOpenProject,
  onOpenExperiment
}) => {
  const { data: serverNotifications, isLoading, error } = useNotifications(50);
  const markAsRead = useMarkNotificationAsRead();
  const markAllAsRead = useMarkAllNotificationsAsRead();

  const notifications = serverNotifications || [];

  const handleOpenEntity = (n: NotificationItem) => {
    if (n.id && !n.is_read && !n.read) {
      markAsRead.mutate(n.id);
    }
    if (n.entity_type === 'project' && n.entity_id && onOpenProject) {
      onOpenProject(n.entity_id);
    } else if (n.entity_type === 'experiment' && n.entity_id && onOpenExperiment) {
      onOpenExperiment(n.entity_id);
    } else if (n.entity_type === 'project') {
      onSelectView('projects');
    } else if (n.entity_type === 'experiment') {
      onSelectView('eln');
    }
  };

  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return 'Recent';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 h-full flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-3" />
        <p className="text-sm font-semibold text-slate-700">Loading Notifications Feed...</p>
        <p className="text-xs text-slate-400 mt-1">Syncing real-time workspace alerts & project assignments</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-12 h-full flex flex-col items-center justify-center">
        <AlertCircle className="w-9 h-9 text-rose-500 mb-3" />
        <p className="text-sm font-semibold text-slate-800">Failed to load notifications</p>
        <p className="text-xs text-slate-500 mt-1">Please check your connection and try again.</p>
      </div>
    );
  }

  const unreadCount = notifications.filter(n => !n.is_read && !n.read).length;

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-800 tracking-tight">Notifications & Collaboration</h2>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-600 text-white">
                  {unreadCount} New
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Live updates on project assignments from Admin/PI, experiment peer reviews, and approvals
            </p>
          </div>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={() => markAllAsRead.mutate()}
            disabled={markAllAsRead.isPending}
            className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3.5 py-2 rounded-xl transition-colors cursor-pointer self-start sm:self-auto"
          >
            <Check className="w-4 h-4 text-emerald-600" />
            <span>Mark All as Read</span>
          </button>
        )}
      </div>

      {/* Notifications List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        {notifications.map((n) => {
          const isUnread = !n.is_read && !n.read;
          const timeStr = formatRelativeTime(n.created_at || n.timestamp);

          return (
            <div
              key={n.id}
              className={`p-5 flex items-start gap-4 transition-colors ${
                isUnread ? 'bg-blue-50/40 hover:bg-blue-50/70' : 'bg-white hover:bg-slate-50'
              }`}
            >
              {/* Type Icon */}
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                n.type === 'assignment' ? 'bg-indigo-100 text-indigo-700' :
                n.type === 'review' || n.type === 'action_required' ? 'bg-amber-100 text-amber-700' :
                n.type === 'status_change' ? 'bg-emerald-100 text-emerald-700' :
                n.type === 'mention' ? 'bg-blue-100 text-blue-700' : 'bg-teal-100 text-teal-700'
              }`}>
                {n.type === 'assignment' && <UserCheck className="w-5 h-5" />}
                {(n.type === 'review' || n.type === 'action_required') && <Clock className="w-5 h-5" />}
                {n.type === 'status_change' && <CheckCircle2 className="w-5 h-5" />}
                {n.type === 'mention' && <MessageSquare className="w-5 h-5" />}
                {n.type === 'ai_summary' && <Sparkles className="w-5 h-5" />}
                {!['assignment', 'review', 'action_required', 'status_change', 'mention', 'ai_summary'].includes(n.type) && (
                  <Bell className="w-5 h-5" />
                )}
              </div>

              {/* Notification Content */}
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-sm ${isUnread ? 'font-bold text-slate-900' : 'font-semibold text-slate-800'}`}>
                      {n.title}
                    </span>
                    {isUnread && (
                      <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                    )}
                    {n.sender_name && (
                      <span className="text-[11px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">
                        From: {n.sender_name}
                      </span>
                    )}
                  </div>
                  <span className="text-slate-400 font-medium text-xs whitespace-nowrap">
                    {timeStr}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  {n.message || n.description}
                </p>

                {/* Quick Action Buttons */}
                <div className="flex items-center gap-3 pt-2">
                  {n.entity_type === 'project' && (
                    <button
                      onClick={() => handleOpenEntity(n)}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                      <FolderKanban className="w-3.5 h-3.5" />
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}

                  {n.entity_type === 'experiment' && (
                    <button
                      onClick={() => handleOpenEntity(n)}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                      <FlaskConical className="w-3.5 h-3.5" />
                      <span>Open Experiment</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}

                  {isUnread && (
                    <button
                      onClick={() => n.id && markAsRead.mutate(n.id)}
                      className="text-[11px] font-medium text-slate-400 hover:text-slate-600 hover:underline transition-all cursor-pointer ml-auto"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {notifications.length === 0 && (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center">
            <Bell className="w-10 h-10 text-slate-300 mb-3" />
            <p className="font-semibold text-slate-700 text-sm">No notifications yet</p>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              You'll be notified here in real-time when an Admin or PI assigns you to projects, or when experiments require review.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
