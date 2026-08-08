export interface ExperimentSummary {
  id: string;
  title: string;
  experiment_number: string;
  status: string;
  updated_at: string;
}

export interface NotificationSummary {
  id: string;
  title: string;
  message: string;
  type: string;
  created_at: string;
  is_read: boolean;
}

export interface QuickAction {
  id: string;
  label: string;
  action_type: string;
  target_url: string;
  icon: string;
  required_permission?: string | null;
}

export interface ActivityFeedItem {
  id: string;
  operation: string;
  entity_type: string;
  description: string;
  performed_by_name?: string | null;
  performed_at: string;
}

export interface AICopilotShortcut {
  shortcut_id: string;
  title: string;
  suggested_prompt: string;
  category: string;
}

export interface DashboardResponse {
  project_count: number;
  active_experiment_count: number;
  completed_experiment_count: number;
  review_required_count: number;
  total_samples_count: number;
  recent_experiments: ExperimentSummary[];
  pending_notifications: NotificationSummary[];
  quick_actions: QuickAction[];
  activity_feed: ActivityFeedItem[];
  ai_copilot_shortcuts: AICopilotShortcut[];
}
