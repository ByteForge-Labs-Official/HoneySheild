import { motion } from 'framer-motion';
import {
  Cpu,
  ExternalLink,
  Power,
  PowerOff,
  RefreshCw,
  Server,
  ShieldCheck,
  Wifi,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { honeypots as mockHoneypots } from '../lib/mock-data';
import { Badge } from '../components/ui/badge';
import { Card } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { useBackend } from '../lib/backend-context';

type Honeypot = {
  id: string;
  name: string;
  status: 'Online' | 'Degraded' | 'Offline';
  ip: string;
  kind?: string;
  host?: string;
  port?: number;
  enabled?: boolean;
  threatsToday?: number;
  uptime?: string;
  flags?: number;
  vendor?: string;
  os?: string;
  services?: string[];
  cpu?: number;
  mem?: number;
  net?: number;
  region?: string;
};

function tone(s: Honeypot['status']) {
  switch (s) {
    case 'Online':
      return {
        badge: 'border-[#00FF88]/50 bg-[#00FF88]/10 text-[#00FF88]',
        dot: 'bg-[#00FF88] shadow-[0_0_10px_rgba(0,255,136,0.7)]',
        card: 'border-[#00FF88]/30',
      };
    case 'Degraded':
      return {
        badge: 'border-amber-400/50 bg-amber-400/10 text-amber-300',
        dot: 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.7)]',
        card: 'border-amber-400/30',
      };
    default:
      return {
        badge: 'border-[#FF3D6E]/50 bg-[#FF3D6E]/10 text-[#FF3D6E]',
        dot: 'bg-[#FF3D6E] shadow-[0_0_10px_rgba(255,61,110,0.7)]',
        card: 'border-[#FF3D6E]/30',
      };
  }
}

export function HoneypotManagement() {
  const {
    honeypots: backendHoneypots,
    events,
    toggleHoneypot,
    usingMock,
    refresh,
    status,
  } = useBackend();

  const mockList: Honeypot[] = useMemo(
    () =>
      mockHoneypots.map((h) => ({
        id: h.id,
        name: h.name,
        status: h.status as Honeypot['status'],
        ip: h.ip,
        kind: h.services?.join(' / '),
        vendor: h.os,
        host: h.ip,
        port: 22,
        enabled: h.status !== 'Offline',
        threatsToday: Math.floor(Math.random() * 50) + 10,
        uptime: h.status === 'Offline' ? '0d' : '5d 12h',
        flags: 0,
        os: h.os,
        services: h.services,
        cpu: h.cpu,
        mem: h.mem,
        net: h.net,
        region: h.region,
      })),
    [],
  );

  const [local, setLocal] = useState<Honeypot[]>(mockList);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Merge backend honeypots into local view.
  useEffect(() => {
    if (backendHoneypots === null) {
      setLocal(mockList);
      return;
    }
    const merged: Honeypot[] = backendHoneypots.map((h) => {
      const today = events
        ? events.filter((e) => e.honeypot_id === h.id).length
        : 0;
      const status: Honeypot['status'] = h.enabled ? 'Online' : 'Offline';
      return {
        id: h.id,
        name: h.name,
        kind: h.kind,
        vendor: h.vendor ?? undefined,
        host: h.host,
        ip: h.host,
        port: h.port,
        enabled: h.enabled,
        status,
        threatsToday: today,
        uptime: h.enabled ? '—' : '0d',
      };
    });
    setLocal(merged);
  }, [backendHoneypots, events, mockList]);

  async function handleToggle(id: string, next: boolean) {
    if (backendHoneypots === null) {
      setLocal((prev) =>
        prev.map((h) =>
          h.id === id
            ? {
                ...h,
                enabled: next,
                status: next ? 'Online' : 'Offline',
              }
            : h,
        ),
      );
      return;
    }
    setBusyId(id);
    setErr(null);
    try {
      await toggleHoneypot(id, next);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Toggle failed');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section id="honeypots" className="container py-12 md:py-16">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-[#00BFFF]/40 bg-[#00BFFF]/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-[#00BFFF]">
            <Server className="h-3 w-3" /> Honeypot Mesh
          </div>
          <h2 className="font-display text-2xl font-semibold tracking-tight text-[#E6F1FF] md:text-3xl">
            Honeypot Fleet Management
          </h2>
          <p className="mt-1 text-sm text-[#8A9BB8]">
            {usingMock
              ? 'Demo fleet — toggle to preview enable/disable behaviour.'
              : `Live fleet — ${local.length} honeypot${local.length === 1 ? '' : 's'} reporting to backend.`}
          </p>
          {err && <p className="mt-1 text-xs text-[#FF3D6E]">{err}</p>}
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          className="inline-flex items-center gap-1.5 rounded-md border border-[#1F2937] bg-[#0A0F1A]/70 px-3 py-1.5 text-xs text-[#E6F1FF] transition hover:border-[#00BFFF]/60"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {local.map((h, i) => {
          const t = tone(h.status);
          const liveData =
            h.threatsToday !== undefined && !usingMock ? h.threatsToday : null;
          const isMock = usingMock || h.threatsToday === undefined;
          return (
            <motion.div
              key={h.id}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ delay: i * 0.05, duration: 0.45 }}
            >
              <Card
                className={`group relative overflow-hidden p-5 transition-colors hover:border-[#00BFFF]/60 ${t.card}`}
              >
                <div className="absolute -right-12 -top-12 h-32 w-32 rounded-full bg-[radial-gradient(circle,rgba(0,229,255,0.18),transparent_60%)] opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-[#00E5FF]" />
                      <h3 className="font-display text-base font-semibold text-[#E6F1FF]">
                        {h.name}
                      </h3>
                    </div>
                    <p className="mt-0.5 text-xs text-[#8A9BB8]">
                      {h.vendor ?? h.os ?? 'Unknown'} · {h.kind ?? 'honeypot'}
                    </p>
                  </div>
                  <Badge variant="outline" className={`uppercase ${t.badge}`}>
                    <span className={`mr-1.5 h-2 w-2 rounded-full ${t.dot}`} />
                    {h.status}
                  </Badge>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#8A9BB8]">Host</p>
                    <p className="font-mono text-[#E6F1FF]">
                      {h.host ?? h.ip}:{h.port ?? 22}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#8A9BB8]">Uptime</p>
                    <p className="font-mono text-[#E6F1FF]">{h.uptime ?? '—'}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#8A9BB8]">Threats today</p>
                    <p className="font-mono text-[#E6F1FF]">
                      {liveData !== null ? liveData : isMock ? Math.floor(Math.random() * 80) + 10 : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-[#8A9BB8]">Region</p>
                    <p className="font-mono text-[#E6F1FF]">{h.region ?? '—'}</p>
                  </div>
                </div>

                <div className="mt-5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-[#8A9BB8]">
                    <Wifi className="h-3.5 w-3.5 text-[#00BFFF]" /> port {h.port ?? 22} open
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] uppercase tracking-wider text-[#8A9BB8]">
                      {h.enabled ? 'Active' : 'Disabled'}
                    </span>
                    <Switch
                      checked={Boolean(h.enabled)}
                      disabled={busyId === h.id || status === 'offline'}
                      onCheckedChange={(v) => void handleToggle(h.id, v)}
                      aria-label={`Toggle ${h.name}`}
                    />
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1 text-[#8A9BB8]">
                    {h.enabled ? (
                      <Power className="h-3.5 w-3.5 text-[#00FF88]" />
                    ) : (
                      <PowerOff className="h-3.5 w-3.5 text-[#FF3D6E]" />
                    )}
                    <span>{h.enabled ? 'Online' : 'Offline'}</span>
                  </div>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-[#00BFFF] transition hover:text-[#00E5FF]"
                  >
                    <ShieldCheck className="h-3.5 w-3.5" /> Inspect
                    <ExternalLink className="h-3 w-3" />
                  </button>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}