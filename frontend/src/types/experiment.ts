export interface ExperimentCollaborator {
  user_id: string;
  role: string;
  id: string;
  added_at: string;
  added_by?: string | null;
}

export interface ExperimentAttachment {
  id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type?: string | null;
  uploaded_by?: string | null;
  created_at: string;
}

export interface Experiment {
  experiment_code: string;
  title: string;
  objective?: string | null;
  hypothesis?: string | null;
  description?: string | null;
  status: string;
  priority: string;
  protocol_id?: string | null;
  start_date?: string | null;
  planned_end_date?: string | null;
  metadata_json: Record<string, any>;
  id: string;
  tenant_id: string;
  organization_id: string;
  project_id: string;
  owner_id?: string | null;
  reviewer_id?: string | null;
  completed_date?: string | null;
  reviewed_date?: string | null;
  is_archived: boolean;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentDetail extends Experiment {
  collaborators: ExperimentCollaborator[];
  attachments: ExperimentAttachment[];
}

export interface ExperimentCreate {
  experiment_code: string;
  title: string;
  objective?: string | null;
  hypothesis?: string | null;
  description?: string | null;
  status?: string;
  priority?: string;
  protocol_id?: string | null;
  start_date?: string | null;
  planned_end_date?: string | null;
  metadata_json?: Record<string, any>;
  project_id?: string | null;
  organization_id?: string | null;
  tenant_id?: string | null;
  owner_id?: string | null;
  reviewer_id?: string | null;
}

export interface ExperimentUpdate {
  title?: string | null;
  objective?: string | null;
  hypothesis?: string | null;
  description?: string | null;
  status?: string | null;
  priority?: string | null;
  protocol_id?: string | null;
  start_date?: string | null;
  planned_end_date?: string | null;
  completed_date?: string | null;
  reviewed_date?: string | null;
  reviewer_id?: string | null;
  metadata_json?: Record<string, any> | null;
}

export interface ExperimentListResponse {
  items: Experiment[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
