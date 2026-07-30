import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity,
  ArrowDownToLine,
  Pause,
  Play,
  Radio,
  ShieldAlert,
  Terminal as TerminalIcon,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  initialFeed,
  makeAttackEvent,
  type AttackEvent as MockAttackEvent,
} from '../lib/mock-data';
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

export function LiveAttackFeed() {
  const { events: backendEvents, status, usingMock } = useBackend();
  const [paused, setPaused] = useState(false);
  const [feed, setFeed] = useState<FeedItem[]>(() =>
    initialFeed().map(toFeedItem),
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const mockTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const liveAttacks: FeedItem[] | null = useMemo(() => {
    if (backendEvents === null) return null;
    return backendEvents.slice(0, 20).map((e) => {
      const protocol = KNOWN_PROTOCOLS.has(e.protocol)
        ? e.protocol
        : 'other';
      const payload =
        (e.payload as Record<string, unknown> | undefined)?.command as
          | string
          | undefined ??
        (e.payload as Record<string, unknown> | undefined)?.uri as
          | string
          | undefined ??
        (e.payload as Record<string, unknown> | undefined)?.path as
          | string
          | undefined ??
        (e.payload as Record<string, unknown> | undefined)?.message as
          | string
          | undefined ??
        (e.payload as Record<string, unknown> | undefined)?.signature as
          | string
          | undefined ??
        (e.event_type ?? `${e.protocol} event`);
      const country = ((e as unknown as { source_country?: string }).source_country ?? 'XX');
      return {
        id: e.id,
        country,
        ip: e.src_ip ?? '0.0.0.0',
        protocol,
        payload: String(payload).slice(0, 120),
        honeypot: e.honeypot_id,
        severity: 'medium',
        time: new Date(e.created_at).getTime() || Date.now(),
      };
    });
  }, [backendEvents]);

  // Backend mode: replace feed with live data.
  useEffect(() => {
    if (liveAttacks) {
      setFeed(liveAttacks);
    }
  }, [liveAttacks]);

  // Mock mode: continuously generate new attacks.
  useEffect(() => {
    if (liveAttacks !== null) {
      if (mockTimer.current) clearInterval(mockTimer.current);
      mockTimer.current = null;
      return;
    }
    if (paused) {
      if (mockTimer.current) clearInterval(mockTimer.current);
      mockTimer.current = null;
      return;
    }
    mockTimer.current = setInterval(() => {
      setFeed((prev) => [toFeedItem(makeAttackEvent()), ...prev].slice(0, 20));
    }, 1400);
    return () => {
      if (mockTimer.current) clearInterval(mockTimer.current);
      mockTimer.current = null;
    };
  }, [paused, liveAttacks]);

  // Auto-scroll on new feed entry.
  useEffect(() => {
    if (!autoScroll || !containerRef.current) return;
    containerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
  }, [feed, autoScroll]);

  const sessionCount = feed.length;

  const statusLabel = useMemo(() => {
    if (liveAttacks !== null) return 'Live Feed — Connected';
    if (status === 'offline') return 'Live Feed — Offline (mock)';
    if (status === 'checking') return 'Live Feed — Connecting…';
    return 'Live Feed — Awaiting Auth';
  }, [status, liveAttacks]);

  const statusColor = liveAttacks
    ? 'text-[#00FF88]'
    : status === 'offline'
      ? 'text-[#FF3D6E]'
      : 'text-amber-300';

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
            onClick={() => setPaused((p) => !p)}
            disabled={liveAttacks !== null}
            className="inline-flex items-center gap-1.5 rounded-md border border-[#1F2937] bg-[#0A0F1A]/70 px-3 py-1.5 text-xs text-[#E6F1FF] transition hover:border-[#00BFFF]/60 disabled:opacity-50"
          >
            {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            {paused ? 'Resume' : 'Pause'}
          </button>
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
            {feed.map((a, idx) => (
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
          {feed.length === 0 && (
            <div className="grid place-items-center py-16 text-sm text-[#8A9BB8]">
              No live events captured yet.
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

function toFeedItem(a: MockAttackEvent): FeedItem {
  return {
    id: a.id,
    country: a.country,
    ip: a.ip,
    protocol: a.protocol,
    payload: a.message,
    honeypot: a.service,
    severity: a.threat,
    time: Date.now(),
  };
}