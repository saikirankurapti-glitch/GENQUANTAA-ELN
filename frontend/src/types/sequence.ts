export interface SequenceVersionRead {
  id: string;
  sequence_id: string;
  version_number: number;
  sequence_data: string;
  length: number;
  gc_content?: number | null;
  change_summary?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface SequenceAnnotationRead {
  id: string;
  sequence_id: string;
  annotation_type: string;
  label: string;
  start_position: number;
  end_position: number;
  strand?: string | null;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface SequenceAttachmentRead {
  id: string;
  sequence_id: string;
  filename: string;
  blob_path: string;
  mime_type?: string | null;
  file_size: number;
  checksum: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface SequenceAnalysisResultRead {
  id: string;
  sequence_id: string;
  analysis_type: string;
  tool_name?: string | null;
  tool_version?: string | null;
  result_summary?: string | null;
  result_json: Record<string, any>;
  performed_by?: string | null;
  created_at: string;
}

export interface SequenceBase {
  sequence_code: string;
  sequence_name: string;
  sequence_type: string;
  source?: string | null;
  molecular_weight?: number | null;
  metadata_json: Record<string, any>;
}

export interface SequenceCreate extends SequenceBase {
  organization_id: string;
  experiment_id?: string | null;
  sample_id?: string | null;
  sequence_data: string;
}

export interface SequenceUpdate {
  sequence_name?: string | null;
  sequence_data?: string | null;
  sequence_type?: string | null;
  source?: string | null;
  molecular_weight?: number | null;
  metadata_json?: Record<string, any> | null;
  change_summary?: string | null;
}

export interface SequenceRead extends SequenceBase {
  id: string;
  tenant_id: string;
  organization_id: string;
  experiment_id?: string | null;
  sample_id?: string | null;
  sequence_data: string;
  length: number;
  gc_content?: number | null;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface SequenceDetail extends SequenceRead {
  seq_versions: SequenceVersionRead[];
  annotations: SequenceAnnotationRead[];
  attachments: SequenceAttachmentRead[];
  analysis_results: SequenceAnalysisResultRead[];
}

export interface SequenceListResponse {
  items: SequenceRead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
