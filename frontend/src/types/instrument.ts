export interface InstrumentTypeRead {
  id: string;
  type_name: string;
  description?: string | null;
}

export interface InstrumentCalibrationRead {
  id: string;
  instrument_id: string;
  calibration_date: string;
  calibrated_by: string;
  certificate_number?: string | null;
  result: string;
  remarks?: string | null;
  next_due_date?: string | null;
}

export interface InstrumentMaintenanceRead {
  id: string;
  instrument_id: string;
  maintenance_type: string;
  maintenance_date: string;
  engineer?: string | null;
  vendor?: string | null;
  remarks?: string | null;
  next_due_date?: string | null;
}

export interface InstrumentReservationRead {
  id: string;
  instrument_id: string;
  reserved_by: string;
  experiment_id?: string | null;
  start_time: string;
  end_time: string;
  status: string;
}

export interface InstrumentUsageRead {
  id: string;
  instrument_id: string;
  operator_id: string;
  experiment_id?: string | null;
  protocol_id?: string | null;
  usage_start: string;
  usage_end?: string | null;
  remarks?: string | null;
}

export interface InstrumentAttachmentRead {
  id: string;
  filename: string;
  blob_path: string;
  mime_type?: string | null;
  file_size: number;
  checksum: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface InstrumentBase {
  instrument_code: string;
  serial_number: string;
  asset_tag: string;
  instrument_name: string;
  manufacturer: string;
  model: string;
  location?: string | null;
  purchase_date?: string | null;
  installation_date?: string | null;
  warranty_expiry?: string | null;
  calibration_due_date?: string | null;
  maintenance_due_date?: string | null;
  operational_status: string;
  availability_status: string;
  metadata_json: Record<string, any>;
}

export interface InstrumentCreate extends InstrumentBase {
  organization_id: string;
  instrument_type_id?: string | null;
}

export interface InstrumentUpdate {
  instrument_name?: string | null;
  location?: string | null;
  calibration_due_date?: string | null;
  maintenance_due_date?: string | null;
  operational_status?: string | null;
  availability_status?: string | null;
  metadata_json?: Record<string, any> | null;
}

export interface InstrumentRead extends InstrumentBase {
  id: string;
  tenant_id: string;
  organization_id: string;
  instrument_type_id?: string | null;
  is_calibration_overdue: boolean;
  is_maintenance_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface InstrumentDetail extends InstrumentRead {
  instrument_type?: InstrumentTypeRead | null;
  calibrations: InstrumentCalibrationRead[];
  maintenances: InstrumentMaintenanceRead[];
  reservations: InstrumentReservationRead[];
  usage_history: InstrumentUsageRead[];
  attachments: InstrumentAttachmentRead[];
}

export interface InstrumentListResponse {
  items: InstrumentRead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
