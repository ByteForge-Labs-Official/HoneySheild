import type { AttackSeverity } from './attack';

export type AlertType =
  | 'bruteforce'
  | 'malware_payload'
  | 'c2_communication'
  | 'credential_stuffing'
  | 'scan'
  | 'exploit'
  | 'anomaly';

export interface Alert {
  id: string;
  created_at: string;
  type: AlertType;
  severity: AttackSeverity;
  title: string;
  description?: string;
  attack_id?: string;
  source_ip?: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
}