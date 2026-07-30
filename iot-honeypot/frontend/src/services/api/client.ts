import axios, { type AxiosInstance, type AxiosError } from 'axios';
import { tokenStorage } from '@/services/storage/tokenStorage';
import type { TokenPair } from '@/types/auth';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 20_000,
  headers: { 'Content-Type': 'application/json' },
});

let isRefreshing = false;
let refreshQueue: Array<(t: string | null) => void> = [];

function processQueue(token: string | null): void {
  refreshQueue.forEach((cb) => cb(token));
  refreshQueue = [];
}

apiClient.interceptors.request.use((cfg) => {
  const token = tokenStorage.getAccessToken();
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

apiClient.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    const original = err.config as any;
    if (
      err.response?.status === 401 &&
      original &&
      !original._retry &&
      tokenStorage.getRefreshToken()
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push((token) => {
            if (!token) reject(err);
            else {
              original.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(original));
            }
          });
        });
      }
      original._retry = true;
      isRefreshing = true;
      try {
        const refresh = tokenStorage.getRefreshToken();
        const { data } = await axios.post<TokenPair>(
          `${BASE_URL}/auth/refresh`,
          { refresh_token: refresh },
        );
        tokenStorage.setTokens(data.access_token, data.refresh_token);
        processQueue(data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(original);
      } catch (refreshErr) {
        processQueue(null);
        tokenStorage.clear();
        if (
          typeof window !== 'undefined' &&
          window.location.pathname !== '/login'
        ) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(err);
  },
);