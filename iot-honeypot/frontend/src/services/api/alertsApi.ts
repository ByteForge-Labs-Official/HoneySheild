import { apiClient } from './client';
import type { Alert } from '@/types/alert';

export const alertsApi = {
  async list(): Promise<Alert[]> {
    const { data } = await apiClient.get<Alert[]>('/alerts');
    return data;
  },
  async acknowledge(id: string): Promise<Alert> {
    const { data } = await apiClient.post<Alert>(`/alerts/${id}/acknowledge`);
    return data;
  },
};