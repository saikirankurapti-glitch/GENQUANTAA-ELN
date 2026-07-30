export interface NotebookTag {
  id: string;
  tag_name: string;
  color: string;
}

export interface NotebookComment {
  id: string;
  comment: string;
  parent_comment_id?: string | null;
  author_id: string;
  created_at: string;
}

export interface NotebookAttachment {
  id: string;
  filename: string;
  blob_path: string;
  mime_type?: string | null;
  file_size: number;
  checksum: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface NotebookEntryVersion {
  id: string;
  notebook_entry_id: string;
  version_number: number;
  content_snapshot: Record<string, any>;
  change_reason?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface NotebookEntry {
  entry_number: string;
  title: string;
  content: Record<string, any>;
  entry_type: string;
  id: string;
  tenant_id: string;
  organization_id: string;
  experiment_id: string;
  ai_summary?: string | null;
  summary_status: string;
  current_version: number;
  is_locked: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotebookEntryDetail extends NotebookEntry {
  versions: NotebookEntryVersion[];
  attachments: NotebookAttachment[];
  comments: NotebookComment[];
  tags: NotebookTag[];
}

export interface NotebookEntryCreate {
  entry_number: string;
  title: string;
  content?: Record<string, any>;
  entry_type?: string;
  experiment_id: string;
  organization_id: string;
}

export interface NotebookEntryUpdate {
  title?: string | null;
  content?: Record<string, any> | null;
  entry_type?: string | null;
  change_reason?: string | null;
}

export interface NotebookListResponse {
  items: NotebookEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
