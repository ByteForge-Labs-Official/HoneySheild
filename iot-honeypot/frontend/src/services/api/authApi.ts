import { apiClient } from './client';
import type {
  AuthUser,
  LoginCredentials,
  RefreshRequest,
  TokenPair,
} from '@/types/auth';

export const authApi = {
  async login(creds: LoginCredentials): Promise<TokenPair> {
    const { data } = await apiClient.post<TokenPair>('/auth/login', creds);
    return data;
  },
  async refresh(refresh_token: string): Promise<TokenPair> {
    const body: RefreshRequest = { refresh_token };
    const { data } = await apiClient.post<TokenPair>('/auth/refresh', body);
    return data;
  },
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  },
  async me(): Promise<AuthUser> {
    const { data } = await apiClient.get<AuthUser>('/auth/me');
    return data;
  },
};