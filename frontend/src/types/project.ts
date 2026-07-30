export interface ProjectCollaborator {
  user_id: string;
  role: string;
  id: string;
  added_at: string;
  added_by?: string | null;
}

export interface ProjectAttachment {
  id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type?: string | null;
  uploaded_by?: string | null;
  created_at: string;
}

export interface Project {
  project_code: string;
  name: string;
  description?: string | null;
  objective?: string | null;
  status: string;
  priority: string;
  tags: string[];
  visibility: string;
  start_date?: string | null;
  target_end_date?: string | null;
  metadata_json: Record<string, any>;
  id: string;
  tenant_id: string;
  organization_id: string;
  owner_id?: string | null;
  completed_date?: string | null;
  is_archived: boolean;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  collaborators: ProjectCollaborator[];
  attachments: ProjectAttachment[];
  experiment_count: number;
}

export interface ProjectCreate {
  project_code: string;
  name: string;
  description?: string | null;
  objective?: string | null;
  status?: string;
  priority?: string;
  tags?: string[];
  visibility?: string;
  start_date?: string | null;
  target_end_date?: string | null;
  metadata_json?: Record<string, any>;
  organization_id: string;
  owner_id?: string | null;
}

export interface ProjectUpdate {
  name?: string | null;
  description?: string | null;
  objective?: string | null;
  status?: string | null;
  priority?: string | null;
  tags?: string[] | null;
  visibility?: string | null;
  start_date?: string | null;
  target_end_date?: string | null;
  completed_date?: string | null;
  metadata_json?: Record<string, any> | null;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
