export type AttackProtocol =
  | 'ssh'
  | 'telnet'
  | 'http'
  | 'https'
  | 'rtsp'
  | 'mqtt'
  | 'modbus'
  | 'upnp'
  | 'other';

export type AttackSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Attack {
  id: string;
  timestamp: string;
  source_ip: string;
  source_port?: number;
  destination_ip?: string;
  destination_port?: number;
  protocol: AttackProtocol;
  honeypot_id: string;
  honeypot_name?: string;
  country?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  severity: AttackSeverity;
  payload_summary?: string;
  username?: string;
  password?: string;
  mitre_tags?: string[];
  raw_event?: Record<string, unknown>;
  /** Raw fields preserved when sourced from the FastAPI backend. */
  src_ip?: string | null;
  src_port?: number | null;
  dst_ip?: string | null;
  dst_port?: number | null;
  event_type?: string;
  created_at?: string;
  payload?: Record<string, unknown>;
  session_id?: string | null;
}

export interface AttackStats {
  total: number;
  by_severity: Record<AttackSeverity, number>;
  by_protocol: Record<AttackProtocol, number>;
  by_country: { country: string; count: number; lat?: number; lon?: number }[];
  timeline: { bucket: string; count: number }[];
  top_ips: { ip: string; count: number; country?: string }[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}