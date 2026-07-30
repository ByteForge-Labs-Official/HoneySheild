import { ComposableMap, Geographies, Geography, Line, Marker } from 'react-simple-maps';
import { motion } from 'framer-motion';
import { useMemo, useState } from 'react';
import {
  initialFeed,
  type AttackEvent,
} from '../lib/mock-data';
import { Card } from '../components/ui/card';
import { SectionHeader } from '../components/fx/SectionHeader';
import { Badge } from '../components/ui/badge';
import { useBackend } from '../lib/backend-context';

const SOURCE = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';
const CENTER: [number, number] = [12.0, 22.0]; // honeypot HQ in central Europe

const COUNTRY_LL: Record<string, [number, number]> = {
  US: [-98, 39], CN: [104, 35], RU: [105, 61], DE: [10, 51], BR: [-51, -14],
  NG: [8, 9], IN: [78, 22], IR: [53, 32], KP: [127, 40], VN: [108, 14],
  TR: [35, 39], MX: [-102, 23], EG: [30, 26], ZA: [22, -30], ID: [113, -2],
  PH: [121, 13], PL: [19, 52], UA: [31, 49], GB: [-3, 55], FR: [2, 46],
  IT: [12, 42], ES: [-3, 40], NL: [5, 52], CA: [-106, 56], SE: [18, 60],
  JP: [138, 36], KR: [127, 36], AU: [133, -25],
};

type Threat = 'low' | 'medium' | 'high' | 'critical';

function threatColor(t: Threat): string {
  switch (t) {
    case 'critical': return '#FF3D6E';
    case 'high': return '#FB923C';
    case 'medium': return '#FACC15';
    default: return '#00FF88';
  }
}

type BackendArc = {
  id: string;
  source_ip: string;
  source_country?: string;
  protocol: string;
  payload?: Record<string, unknown>;
};

export function WorldMap() {
  const { events: backendEvents, usingMock } = useBackend();
  const [hover, setHover] = useState<AttackEvent | null>(null);

  const events: AttackEvent[] = useMemo(() => {
    if (backendEvents && backendEvents.length > 0) {
      const raw = backendEvents as unknown as BackendArc[];
      return raw.slice(0, 26).map((e, i) => {
        const iso = (e.source_country ?? '').toUpperCase();
        const ll = COUNTRY_LL[iso] ?? [
          Math.random() * 360 - 180,
          Math.random() * 140 - 60,
        ];
        const sev = (['low', 'medium', 'high', 'critical'] as Threat[])[
          Math.min(3, i % 4)
        ];
        const payloadSummary =
          (e.payload?.command as string | undefined) ??
          (e.payload?.uri as string | undefined) ??
          (e.payload?.message as string | undefined) ??
          `${e.protocol} event`;
        return {
          id: e.id,
          ip: e.source_ip,
          lat: ll[1],
          lng: ll[0],
          countryName: e.source_country ?? 'Unknown',
          country: e.source_country ?? 'XX',
          protocol: e.protocol,
          threat: sev,
          message: payloadSummary,
          timestamp: new Date().toISOString(),
          service: e.protocol,
          status: 'Logged' as const,
        };
      });
    }
    return initialFeed();
  }, [backendEvents]);

  const arcs = useMemo(
    () =>
      events.slice(0, 26).map((e) => ({
        id: e.id,
        start: [e.lng, e.lat] as [number, number],
        end: CENTER,
        threat: e.threat,
        ip: e.ip,
        proto: e.protocol,
        color: threatColor(e.threat),
      })),
    [events]
  );

  return (
    <section id="map" className="container py-12 md:py-16">
      <SectionHeader
        eyebrow="Geographic Intelligence"
        title="Interactive Threat Map"
        subtitle={
          usingMock
            ? 'Every attack source pulses as data flows toward the honeypot mesh.'
            : 'Live arcs traced from attackers to the honeypot mesh.'
        }
        right={
          <div className="flex items-center gap-2">
            <Badge variant="danger">Critical</Badge>
            <Badge variant="warning">High</Badge>
            <Badge variant="default">Medium</Badge>
            <Badge variant="success">Low</Badge>
          </div>
        }
      />
      <Card className="relative h-[480px] overflow-hidden p-0">
        <div className="absolute inset-0 hex-pattern opacity-30" />
        <ComposableMap
          projectionConfig={{ scale: 155 }}
          width={980}
          height={480}
          style={{ width: '100%', height: '100%', background: 'transparent' }}
        >
          <defs>
            <linearGradient id="arc-gradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#00BFFF" stopOpacity="0" />
              <stop offset="50%" stopColor="#00E5FF" stopOpacity="1" />
              <stop offset="100%" stopColor="#00FF88" stopOpacity="0" />
            </linearGradient>
            <radialGradient id="pulse-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#00FF88" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#00FF88" stopOpacity="0" />
            </radialGradient>
          </defs>
          <Geographies geography={SOURCE}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  style={{
                    default: {
                      fill: '#0F1626',
                      stroke: '#1F2A44',
                      strokeWidth: 0.5,
                      outline: 'none',
                    },
                    hover: {
                      fill: '#14223a',
                      stroke: '#00BFFF',
                      strokeWidth: 0.6,
                      outline: 'none',
                    },
                    pressed: { fill: '#0F1626', outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>

          {/* Arc lines */}
          {arcs.map((a) => (
            <Line
              key={a.id}
              from={a.start}
              to={a.end}
              stroke="url(#arc-gradient)"
              strokeWidth={1.2}
              strokeLinecap="round"
            >
              <animate attributeName="stroke-dashoffset" from="200" to="0" dur="2s" repeatCount="indefinite" />
            </Line>
          ))}

          {/* Attack origin pulses */}
          {arcs.map((a) => (
            <Marker key={`m-${a.id}`} coordinates={a.start}>
              <circle r={3} fill={a.color} />
              <motion.circle
                r={3}
                fill="transparent"
                stroke={a.color}
                strokeWidth={1}
                initial={{ scale: 1, opacity: 0.7 }}
                animate={{ scale: 4, opacity: 0 }}
                transition={{ duration: 2, repeat: Infinity }}
                style={{ transformOrigin: 'center' }}
              />
            </Marker>
          ))}

          {/* Honeypot center */}
          <Marker coordinates={CENTER}>
            <circle r={6} fill="#00FF88" />
            <circle r={12} fill="transparent" stroke="#00FF88" strokeOpacity={0.6} strokeWidth={1}>
              <animate attributeName="r" values="10;18;10" dur="2.4s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" values="0.8;0;0.8" dur="2.4s" repeatCount="indefinite" />
            </circle>
            <text textAnchor="middle" y={-16} fill="#00FF88" fontSize={10} fontFamily="monospace">
              HONEMESH • EU
            </text>
          </Marker>
        </ComposableMap>

        {hover && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute right-4 top-4 w-60 rounded-lg border border-[#00BFFF]/40 bg-[#0B0F19]/90 p-4 shadow-neon"
          >
            <p className="text-xs font-mono text-[#00E5FF]">{hover.ip}</p>
            <p className="mt-1 text-sm font-semibold text-[#E6F1FF]">{hover.countryName}</p>
            <div className="mt-3 space-y-1 text-xs text-[#8A9BB8]">
              <p>
                Threat: <span className="text-[#E6F1FF] uppercase">{hover.threat}</span>
              </p>
              <p>
                Top protocol: <span className="text-[#E6F1FF]">{hover.protocol}</span>
              </p>
            </div>
          </motion.div>
        )}

        <button
          className="absolute left-4 bottom-4 rounded-md border border-[#00BFFF]/40 bg-[#0B0F19]/80 px-3 py-1.5 text-[10px] uppercase tracking-wider text-[#00BFFF] hover:bg-[#00BFFF]/10"
          onMouseEnter={() => setHover(events[0] ?? null)}
          onMouseLeave={() => setHover(null)}
        >
          {usingMock ? 'Hover region for intel' : 'Hover region for live intel'}
        </button>
      </Card>
    </section>
  );
}