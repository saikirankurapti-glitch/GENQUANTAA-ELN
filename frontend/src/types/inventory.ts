export interface InventoryCategory {
  id: string;
  name: string;
  code: string;
  description?: string | null;
}

export interface InventorySupplier {
  id: string;
  name: string;
  contact_email?: string | null;
  contact_phone?: string | null;
}

export interface InventoryLocation {
  id: string;
  name: string;
  building?: string | null;
  room?: string | null;
  cabinet_shelf?: string | null;
}

export interface InventoryBatch {
  id: string;
  inventory_item_id: string;
  lot_number: string;
  batch_quantity: number;
  manufacture_date?: string | null;
  expiry_date?: string | null;
  status: string;
}

export interface InventoryTransaction {
  id: string;
  inventory_item_id: string;
  transaction_type: string;
  quantity: number;
  performed_by?: string | null;
  performed_at: string;
  remarks?: string | null;
}

export interface InventoryItem {
  item_code: string;
  item_name: string;
  unit: string;
  minimum_stock: number;
  reorder_level: number;
  lot_number?: string | null;
  expiry_date?: string | null;
  status: string;
  metadata_json: Record<string, any>;
  id: string;
  tenant_id: string;
  organization_id: string;
  category_id?: string | null;
  supplier_id?: string | null;
  storage_location_id?: string | null;
  current_stock: number;
  is_low_stock: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryItemDetail extends InventoryItem {
  category?: InventoryCategory | null;
  supplier?: InventorySupplier | null;
  storage_location?: InventoryLocation | null;
  batches: InventoryBatch[];
  transactions: InventoryTransaction[];
}

export interface InventoryItemCreate {
  item_code: string;
  item_name: string;
  unit?: string;
  minimum_stock?: number;
  reorder_level?: number;
  lot_number?: string | null;
  expiry_date?: string | null;
  status?: string;
  metadata_json?: Record<string, any>;
  organization_id: string;
  category_id?: string | null;
  supplier_id?: string | null;
  storage_location_id?: string | null;
  initial_stock?: number;
}

export interface InventoryItemUpdate {
  item_name?: string | null;
  unit?: string | null;
  minimum_stock?: number | null;
  reorder_level?: number | null;
  storage_location_id?: string | null;
  status?: string | null;
  metadata_json?: Record<string, any> | null;
}

export interface InventoryReceiveRequest {
  quantity: number;
  lot_number?: string | null;
  expiry_date?: string | null;
  remarks?: string | null;
}

export interface InventoryIssueRequest {
  quantity: number;
  remarks?: string | null;
}

export interface InventoryListResponse {
  items: InventoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
