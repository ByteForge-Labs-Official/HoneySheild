import type { Attack, AttackStats } from '@/types/attack';

const PROTO = ['ssh', 'telnet', 'http', 'rtsp', 'mqtt', 'modbus'] as const;
const COUNTRIES = [
  { c: 'CN', n: 'China', lat: 35.86, lon: 104.19 },
  { c: 'US', n: 'United States', lat: 37.09, lon: -95.71 },
  { c: 'RU', n: 'Russia', lat: 61.52, lon: 105.32 },
  { c: 'BR', n: 'Brazil', lat: -14.24, lon: -51.93 },
  { c: 'IN', n: 'India', lat: 20.59, lon: 78.96 },
  { c: 'DE', n: 'Germany', lat: 51.16, lon: 10.45 },
  { c: 'NG', n: 'Nigeria', lat: 9.08, lon: 8.67 },
  { c: 'KP', n: 'North Korea', lat: 40.34, lon: 127.51 },
  { c: 'IR', n: 'Iran', lat: 32.43, lon: 53.69 },
  { c: 'VN', n: 'Vietnam', lat: 14.06, lon: 108.28 },
];

function pseudoRand(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

export function generateDemoAttack(seed = Date.now()): Attack {
  const r = pseudoRand(seed);
  const country = COUNTRIES[Math.floor(r() * COUNTRIES.length)];
  const protocol = PROTO[Math.floor(r() * PROTO.length)];
  const sev = (['low', 'medium', 'high', 'critical'] as const)[
    Math.floor(r() * 4)
  ];
  const id = `atc_${Math.floor(r() * 1e10).toString(16)}`;
  return {
    id,
    timestamp: new Date().toISOString(),
    source_ip: `${Math.floor(r() * 255)}.${Math.floor(r() * 255)}.${Math.floor(
      r() * 255,
    )}.${Math.floor(r() * 255)}`,
    protocol,
    honeypot_id: `hp_${protocol}`,
    honeypot_name: `${protocol.toUpperCase()} honeypot`,
    country: country.c,
    city: country.n,
    latitude: country.lat + (r() - 0.5) * 5,
    longitude: country.lon + (r() - 0.5) * 5,
    severity: sev,
    payload_summary: 'cmd injection attempt',
    username: 'root',
    password: 'admin',
    mitre_tags: ['T1110', 'T1059'],
  };
}

export function generateDemoStats(): AttackStats {
  const by_country = COUNTRIES.map(({ c, lat, lon }) => ({
    country: c,
    count: Math.floor(Math.random() * 800) + 50,
    lat,
    lon,
  }));
  const timeline = Array.from({ length: 24 }, (_, i) => ({
    bucket: new Date(Date.now() - (23 - i) * 3600_000).toISOString(),
    count: Math.floor(Math.random() * 80) + 10,
  }));
  const top_ips = Array.from({ length: 10 }, () => ({
    ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(
      Math.random() * 255,
    )}.${Math.floor(Math.random() * 255)}`,
    count: Math.floor(Math.random() * 200) + 30,
    country: COUNTRIES[Math.floor(Math.random() * COUNTRIES.length)].c,
  }));
  return {
    total: 12487,
    by_severity: { low: 4500, medium: 5000, high: 2200, critical: 787 },
    by_protocol: { ssh: 4000, telnet: 3000, http: 2500, rtsp: 800, mqtt: 1200, modbus: 600, other: 387 } as any,
    by_country,
    timeline,
    top_ips,
  };
}