import { apiClient } from './client';
import type { Attack, AttackStats, Page } from '@/types/attack';

export const attacksApi = {
  async list(params?: {
    page?: number;
    page_size?: number;
    protocol?: string;
    severity?: string;
  }): Promise<Page<Attack>> {
    const { data } = await apiClient.get<Page<Attack>>('/attacks', { params });
    return data;
  },
  async stats(): Promise<AttackStats> {
    const { data } = await apiClient.get<AttackStats>('/analytics/stats');
    return data;
  },
  async timeline(range: '1h' | '24h' | '7d' | '30d' = '24h') {
    const { data } = await apiClient.get('/analytics/timeline', {
      params: { range },
    });
    return data as { bucket: string; count: number }[];
  },
  async topIps(limit = 10) {
    const { data } = await apiClient.get('/analytics/top-ips', {
      params: { limit },
    });
    return data as { ip: string; count: number; country?: string }[];
  },
  async geo() {
    const { data } = await apiClient.get('/analytics/geo');
    return data;
  },
  async get(id: string): Promise<Attack> {
    const { data } = await apiClient.get<Attack>(`/attacks/${id}`);
    return data;
  },
};