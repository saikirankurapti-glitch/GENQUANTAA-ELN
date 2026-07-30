export interface SampleType {
  id: string;
  name: string;
  code: string;
  description?: string | null;
}

export interface StorageLocation {
  id: string;
  name: string;
  building?: string | null;
  room?: string | null;
  freezer_unit?: string | null;
  shelf_box?: string | null;
}

export interface ChainOfCustody {
  id: string;
  sample_id: string;
  action: string;
  custodian_id: string;
  performed_at: string;
  remarks?: string | null;
}

export interface SampleAttachment {
  id: string;
  filename: string;
  blob_path: string;
  mime_type?: string | null;
  file_size: number;
  checksum: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface Sample {
  sample_code: string;
  barcode: string;
  sample_name: string;
  quantity: number;
  unit: string;
  concentration?: string | null;
  storage_temperature: string;
  collection_date?: string | null;
  expiry_date?: string | null;
  status: string;
  metadata_json: Record<string, any>;
  id: string;
  tenant_id: string;
  organization_id: string;
  experiment_id: string;
  sample_type_id?: string | null;
  storage_location_id?: string | null;
  parent_sample_id?: string | null;
  is_archived: boolean;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SampleDetail extends Sample {
  chain_of_custody: ChainOfCustody[];
  attachments: SampleAttachment[];
  storage_location?: StorageLocation | null;
  sample_type?: SampleType | null;
}

export interface SampleCreate {
  sample_code: string;
  barcode: string;
  sample_name: string;
  quantity?: number;
  unit?: string;
  concentration?: string | null;
  storage_temperature?: string;
  collection_date?: string | null;
  expiry_date?: string | null;
  status?: string;
  metadata_json?: Record<string, any>;
  experiment_id: string;
  organization_id: string;
  sample_type_id?: string | null;
  storage_location_id?: string | null;
  parent_sample_id?: string | null;
}

export interface SampleUpdate {
  sample_name?: string | null;
  quantity?: number | null;
  unit?: string | null;
  concentration?: string | null;
  storage_temperature?: string | null;
  storage_location_id?: string | null;
  expiry_date?: string | null;
  status?: string | null;
  metadata_json?: Record<string, any> | null;
}

export interface SampleListResponse {
  items: Sample[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
