export type ViewMode = 
  | 'landing'
  | 'login'
  | 'dashboard'
  | 'projects'
  | 'project_detail'
  | 'experiments'
  | 'eln'
  | 'samples'
  | 'sample-detail'
  | 'protocols'
  | 'protocol-detail'
  | 'inventory'
  | 'inventory-detail'
  | 'instruments'
  | 'instrument-detail'
  | 'sequence-registry'
  | 'sequence-detail'
  | 'sequences'
  | 'ai-copilot'
  | 'search'
  | 'reports'
  | 'notifications'
  | 'settings'
  | 'admin'
  | 'integrations'
  | 'audit'
  | 'files';

export type UserPersona = 
  | 'Bench Scientist (Researcher)'
  | 'Lab Manager / PI'
  | 'Bioinformatician'
  | 'QA / Compliance Auditor'
  | 'Admin (IT/Ops)';

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  password?: string;
  role: 'Scientist' | 'Lab Technician' | 'PI / Manager' | 'Bioinformatician' | 'Admin';
  persona: UserPersona;
  avatar: string;
  department: string;
  active: boolean;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  category: 'Molecular Biology' | 'Neuroscience' | 'Vaccine Dev' | 'Plant Genomics' | 'Gene Editing';
  status: 'Active' | 'Completed' | 'On Hold' | 'Archived';
  experimentsCount: number;
  members: string[];
  tags: string[];
  updatedAt: string;
  progress: number;
}

export interface MaterialItem {
  id: string;
  name: string;
  sampleId?: string;
  quantity: string;
  lotNumber: string;
}

export interface ExperimentSummary {
  objective: string;
  method: string;
  result: string;
  conclusion: string;
  citations: { text: string; linkId: string }[];
}

export interface NotebookVersion {
  version: number;
  timestamp: string;
  author: string;
  changes: string;
}

export interface Experiment {
  id: string;
  title: string;
  projectId: string;
  projectName: string;
  author: string;
  status: 'Planned' | 'In Progress' | 'Completed' | 'Reviewed';
  date: string;
  objective: string;
  materials: MaterialItem[];
  protocolSteps: string[];
  results: string;
  summary?: ExperimentSummary;
  version: number;
  versionHistory: NotebookVersion[];
  isSoftDeleted?: boolean;
  attachmentsCount: number;
  commentsCount: number;
  tags: string[];
}

export interface Sample {
  id: string;
  name: string;
  type: 'Cell Line' | 'Plasmid' | 'Reagent' | 'RNA Sample' | 'Protein' | 'Tissue';
  projectId: string;
  projectName: string;
  status: 'Available' | 'Low Stock' | 'Depleted' | 'Quarantine';
  location: {
    freezer: string;
    shelf: string;
    rack: string;
    box: string;
    position: string;
  };
  barcode: string;
  createdDate: string;
  creator: string;
  quantity: string;
}

export interface SequenceRecord {
  id: string;
  name: string;
  organism: string;
  type: 'DNA' | 'RNA' | 'Protein';
  sequence: string;
  length: number;
  gcContent: number;
  molecularWeightKgMol: number;
  createdDate: string;
  features: { name: string; start: number; end: number; color: string }[];
}

export interface AIChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  confidenceScore?: number; // Section 3.8 Confidence Indicator (e.g. 96%)
  citations?: { id: string; label: string; viewTarget: ViewMode }[];
  suggestedActions?: string[];
  protocolData?: {
    title: string;
    sopCode: string;
    safetyPrecautions: string;
    steps: string[];
  };
}

export interface NotificationItem {
  id: string;
  title: string;
  message?: string;
  description?: string;
  timestamp?: string;
  created_at?: string;
  type: 'mention' | 'assignment' | 'review' | 'status_change' | 'ai_summary' | 'info' | 'action_required' | string;
  read?: boolean;
  is_read?: boolean;
  user?: string;
  sender_name?: string;
  entity_type?: 'project' | 'experiment' | 'protocol' | 'sample' | 'notebook' | string;
  entity_id?: string;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  targetObject: string;
  objectType: string;
  details: string;
  ipAddress: string;
}

export interface IntegrationService {
  id: string;
  name: string;
  category: 'Cloud Storage' | 'Communication' | 'Lab Instruments' | 'Scientific DB';
  connected: boolean;
  icon: string;
  description: string;
}

export interface FileItem {
  id: string;
  name: string;
  type: 'FASTA' | 'CSV' | 'PDF' | 'Image' | 'Excel' | 'Doc';
  size: string;
  modifiedDate: string;
  owner: string;
  sharedWith: string[];
}

export interface QACommentReply {
  id: string;
  author_id: string;
  author_name: string;
  author_role: string;
  comment: string;
  created_at: string;
}

export interface QAComment {
  id: string;
  experiment_id: string;
  author_id: string;
  author_name: string;
  author_role: string;
  section_id: string;
  section_title?: string;
  target_text?: string;
  comment: string;
  category: 'QA_REVIEW' | 'COMPLIANCE_CHECK' | 'SCIENTIFIC_QUESTION' | 'SUGGESTION' | string;
  status: 'open' | 'resolved';
  resolved_by?: string;
  resolved_at?: string;
  resolution_note?: string;
  created_at: string;
  replies: QACommentReply[];
}

export interface QACommentCreate {
  section_id: string;
  section_title?: string;
  target_text?: string;
  comment: string;
  category?: string;
}
