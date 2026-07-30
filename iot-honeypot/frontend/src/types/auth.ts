export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'analyst' | 'viewer';
  full_name?: string;
}

export interface RefreshRequest {
  refresh_token: string;
}