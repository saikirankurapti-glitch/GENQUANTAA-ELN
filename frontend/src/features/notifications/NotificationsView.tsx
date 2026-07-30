import React from 'react';
import type { NotificationItem, ViewMode } from '../../types';
import { MessageSquare, CheckCircle2, UserCheck, Sparkles, Check } from 'lucide-react';

interface NotificationsViewProps {
  notifications: NotificationItem[];
  onMarkAllAsRead: () => void;
  onSelectView: (view: ViewMode) => void;
}

export const NotificationsView: React.FC<NotificationsViewProps> = ({
  notifications,
  onMarkAllAsRead
}) => {
  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Notifications & Collaboration Feed</h2>
          <p className="text-xs text-slate-500">Mentions, experiment status updates, and AI copilot protocol digests</p>
        </div>

        <button
          onClick={onMarkAllAsRead}
          className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition-colors cursor-pointer"
        >
          <Check className="w-4 h-4 text-emerald-600" />
          <span>Mark All as Read</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 flex items-start gap-4 transition-colors ${
              n.read ? 'bg-white' : 'bg-blue-50/40 font-medium'
            }`}
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              n.type === 'mention' ? 'bg-blue-100 text-blue-600' :
              n.type === 'status_change' ? 'bg-emerald-100 text-emerald-600' :
              n.type === 'assignment' ? 'bg-indigo-100 text-indigo-600' : 'bg-teal-100 text-teal-600'
            }`}>
              {n.type === 'mention' && <MessageSquare className="w-5 h-5" />}
              {n.type === 'status_change' && <CheckCircle2 className="w-5 h-5" />}
              {n.type === 'assignment' && <UserCheck className="w-5 h-5" />}
              {n.type === 'ai_summary' && <Sparkles className="w-5 h-5" />}
            </div>

            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-800">{n.title}</span>
                <span className="text-slate-400 font-mono text-[11px]">{n.timestamp}</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{n.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
