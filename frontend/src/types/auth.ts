export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  date_of_birth?: string | null;
  gender?: string | null;
  department?: string | null;
  designation?: string | null;
  location?: string | null;
  time_zone?: string | null;
  language?: string | null;
  avatar_url?: string | null;
  biography?: string | null;
  id: string;
  user_id: string;
}

export interface UserRole {
  role_id: string;
  expires_at?: string | null;
  is_primary: boolean;
  is_active: boolean;
  id: string;
  user_id: string;
  assigned_by?: string | null;
  assigned_at: string;
}

export interface User {
  username: string;
  email: string;
  employee_id?: string | null;
  first_name: string;
  last_name: string;
  display_name?: string | null;
  phone_number?: string | null;
  id: string;
  tenant_id: string;
  organization_id?: string | null;
  must_change_password: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  is_active: boolean;
  is_locked: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  profile?: UserProfile | null;
  roles: UserRole[];
}

export interface LoginRequest {
  username_or_email: string;
  password: string;
  mfa_code?: string | null;
  device_identifier?: string | null;
  device_name?: string | null;
}

export interface RegisterRequest {
  first_name: string;
  last_name: string;
  email: string;
  password?: string;
}
