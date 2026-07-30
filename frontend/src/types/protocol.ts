export interface ProtocolStep {
  step_number: number;
  title: string;
  instructions: string;
  duration_minutes?: number | null;
  safety_notes?: string | null;
}

export interface ProtocolStepCreate extends ProtocolStep {}

export interface ProtocolStepRead extends ProtocolStep {
  id: string;
  protocol_id: string;
}

export interface ProtocolApproval {
  status: string;
  comments?: string | null;
}

export interface ProtocolApprovalCreate extends ProtocolApproval {}

export interface ProtocolApprovalRead extends ProtocolApproval {
  id: string;
  protocol_id: string;
  approver_id: string;
  decision_date: string;
}

export interface ProtocolAttachment {
  id: string;
  filename: string;
  blob_path: string;
  mime_type?: string | null;
  file_size: number;
  checksum: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface ProtocolVersion {
  id: string;
  protocol_id: string;
  version_number: number;
  content_snapshot: Record<string, any>;
  change_reason?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface Protocol {
  protocol_code: string;
  title: string;
  description?: string | null;
  category: string;
  status: string;
  metadata_json: Record<string, any>;
  id: string;
  tenant_id: string;
  organization_id: string;
  current_version: number;
  owner_id?: string | null;
  reviewer_id?: string | null;
  approval_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProtocolDetail extends Protocol {
  steps: ProtocolStepRead[];
  versions: ProtocolVersion[];
  attachments: ProtocolAttachment[];
  approvals: ProtocolApprovalRead[];
}

export interface ProtocolCreate {
  protocol_code: string;
  title: string;
  description?: string | null;
  category?: string;
  status?: string;
  metadata_json?: Record<string, any>;
  organization_id: string;
  reviewer_id?: string | null;
  steps?: ProtocolStepCreate[];
}

export interface ProtocolUpdate {
  title?: string | null;
  description?: string | null;
  category?: string | null;
  reviewer_id?: string | null;
  metadata_json?: Record<string, any> | null;
  change_reason?: string | null;
}

export interface ProtocolListResponse {
  items: Protocol[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
