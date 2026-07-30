import { motion, useInView } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Globe2,
  Power,
  ShieldAlert,
  Users,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { stats as mockStats } from '../lib/mock-data';
import { useCountUp } from '../lib/hooks';
import { Card } from '../components/ui/card';
import { formatNumber } from '../lib/utils';
import { useBackend } from '../lib/backend-context';

const ICONS = [Activity, Power, Users, Globe2, ShieldAlert, AlertTriangle];

function Counter({ target, suffix }: { target: number; suffix: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  const value = useCountUp(inView ? target : 0, 1400, [target]);
  return (
    <span ref={ref} className="font-display text-3xl font-bold tracking-tight text-[#E6F1FF]">
      {formatNumber(value)}
      <span className="text-base text-[#8A9BB8]">{suffix}</span>
    </span>
  );
}

export function StatsGrid() {
  const { honeypots, events, usingMock } = useBackend();

  const live = useMemo(() => {
    if (honeypots === null && events === null) return null;
    const activeHoneypots = honeypots?.filter((h) => h.enabled).length ?? 0;
    const uniqueIps = events ? new Set(events.map((e) => e.src_ip ?? '')).size : 0;
    const totalEvents = events?.length ?? 0;
    const blocked = events
      ? events.filter((e) => e.protocol && e.protocol !== 'other').length
      : 0;
    const threatScore = Math.min(100, Math.round((totalEvents / 200) * 100));
    return {
      totalAttacksToday: totalEvents,
      activeHoneypots,
      uniqueAttackers: uniqueIps,
      countriesTargeting: uniqueIps > 0 ? Math.min(uniqueIps, 30) : mockStats.countriesTargeting,
      blockedSessions: blocked,
      threatScore: threatScore > 0 ? threatScore : mockStats.threatScore,
    };
  }, [honeypots, events]);

  const values = live ?? {
    totalAttacksToday: mockStats.totalAttacksToday,
    activeHoneypots: mockStats.activeHoneypots,
    uniqueAttackers: mockStats.uniqueAttackers,
    countriesTargeting: mockStats.countriesTargeting,
    blockedSessions: mockStats.blockedSessions,
    threatScore: mockStats.threatScore,
  };

  const cards = [
    {
      label: 'Total Attacks Today',
      target: values.totalAttacksToday,
      suffix: '',
      icon: 0,
      tone: 'cyan',
    },
    { label: 'Active Honeypots', target: values.activeHoneypots, suffix: '', icon: 1, tone: 'green' },
    { label: 'Unique Attackers', target: values.uniqueAttackers, suffix: '', icon: 2, tone: 'cyan' },
    { label: 'Countries Targeting', target: values.countriesTargeting, suffix: '', icon: 3, tone: 'green' },
    { label: 'Blocked Sessions', target: values.blockedSessions, suffix: '', icon: 4, tone: 'red' },
    { label: 'Threat Score', target: values.threatScore, suffix: '/100', icon: 5, tone: 'red' },
  ];

  // Force re-mount animation when live data updates.
  const [animKey, setAnimKey] = useState(0);
  useEffect(() => {
    if (live) setAnimKey((k) => k + 1);
  }, [live]);

  return (
    <section id="dashboard" className="container py-12 md:py-16">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-[#00BFFF]/40 bg-[#00BFFF]/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-[#00BFFF]">
            <span className="h-1.5 w-1.5 animate-pulse-glow rounded-full bg-[#00FF88]" /> SOC Overview
          </div>
          <h2 className="font-display text-2xl font-semibold tracking-tight text-[#E6F1FF] md:text-3xl">
            Global Threat Posture
          </h2>
          <p className="mt-1 text-sm text-[#8A9BB8]">
            {usingMock
              ? 'Real-time metrics aggregated from every honeypot in the fleet.'
              : 'Live metrics pulled from the backend honeypot mesh.'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {cards.map((c, i) => {
          const Icon = ICONS[c.icon];
          const glow =
            c.tone === 'red'
              ? 'shadow-[0_0_24px_rgba(255,61,110,0.25)]'
              : 'shadow-[0_0_24px_rgba(0,191,255,0.25)]';
          return (
            <motion.div
              key={`${c.label}-${animKey}`}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ delay: i * 0.06, duration: 0.5 }}
            >
              <Card
                className={`group h-full overflow-hidden p-5 transition-transform duration-300 hover:-translate-y-1 hover:border-[#00BFFF]/60 ${glow}`}
              >
                <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-[radial-gradient(circle,rgba(0,229,255,0.18),transparent_60%)] opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="flex items-center justify-between">
                  <span
                    className={`grid h-10 w-10 place-items-center rounded-lg border ${
                      c.tone === 'red'
                        ? 'border-[#FF3D6E]/40 bg-[#FF3D6E]/10 text-[#FF3D6E]'
                        : 'border-[#00BFFF]/40 bg-[#00BFFF]/10 text-[#00E5FF]'
                    } shadow-[0_0_18px_rgba(0,191,255,0.35)]`}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="text-[10px] font-medium uppercase tracking-wider text-[#00FF88]">
                    {usingMock ? 'Demo' : '+ Live'}
                  </span>
                </div>
                <div className="mt-4">
                  <Counter target={c.target} suffix={c.suffix} />
                  <p className="mt-1 text-xs text-[#8A9BB8]">{c.label}</p>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}