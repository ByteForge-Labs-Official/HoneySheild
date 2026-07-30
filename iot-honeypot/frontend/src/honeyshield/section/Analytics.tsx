import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { motion } from 'framer-motion';
import { Activity, Globe, Network, Server, Shield, TrendingUp } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import {
  attacksPerHour,
  countriesByAttacks,
  osDetected,
  topPorts,
  topProtocols,
} from '../lib/mock-data';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Download, FileBarChart } from 'lucide-react';
import { useBackend } from '../lib/backend-context';
import { socApi, type TimelineBucket } from '../lib/soc-api';

type Range = '1h' | '24h' | '7d' | '30d';
const RANGE_MULTIPLIER: Record<Range, number> = {
  '1h': 0.25,
  '24h': 1,
  '7d': 2.4,
  '30d': 4.8,
};

const tooltipStyle = {
  contentStyle: {
    background: '#0B0F19',
    border: '1px solid #1F2A44',
    borderRadius: 10,
    color: '#E6F1FF',
    fontSize: 12,
    boxShadow: '0 0 18px rgba(0,191,255,0.25)',
  },
  labelStyle: { color: '#8A9BB8' },
};

function AnalyticsCard({
  title,
  description,
  icon: Icon,
  delay,
  children,
}: {
  title: string;
  description: string;
  icon: any;
  delay: number;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ y: -2 }}
    >
      <Card className="h-full transition-colors hover:border-[#00BFFF]/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{title}</CardTitle>
            <span className="grid h-8 w-8 place-items-center rounded-md border border-[#00BFFF]/40 bg-[#00BFFF]/10 text-[#00E5FF]">
              <Icon className="h-4 w-4" />
            </span>
          </div>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="h-[260px]">{children}</CardContent>
      </Card>
    </motion.div>
  );
}

export function Analytics() {
  const [range, setRange] = useState<Range>('24h');
  const [bucket, setBucket] = useState<'all' | 'attacks' | 'blocked'>('all');
  const { timeline, geo, analytics, usingMock } = useBackend();
  const [liveTimeline, setLiveTimeline] = useState<TimelineBucket[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (usingMock) {
      setLiveTimeline(null);
      return;
    }
    void socApi.fetchAnalyticsTimeline(range).then((data) => {
      if (!cancelled) setLiveTimeline(data);
    });
    return () => {
      cancelled = true;
    };
  }, [range, usingMock]);

  const mul = RANGE_MULTIPLIER[range];

  const liveHourData = useMemo(() => {
    if (!timeline || timeline.length === 0) return null;
    return timeline.map((b, i) => {
      const dt = new Date(b.bucket);
      const hour = Number.isNaN(dt.getTime())
        ? String(i)
        : dt.toISOString().slice(5, 16).replace('T', ' ');
      const attacks = b.count;
      return {
        hour,
        attacks,
        blocked: Math.round(attacks * 0.62),
        unique: Math.round(attacks * 0.4),
      };
    });
  }, [timeline]);

  const hourData = useMemo(
    () =>
      (liveHourData ?? attacksPerHour).map((d) => ({
        hour: d.hour,
        attacks: Math.round(d.attacks * mul),
        blocked: Math.round(d.blocked * mul),
        unique: Math.round(d.unique * mul),
      })),
    [liveHourData, mul],
  );

  const portData = useMemo(
    () => topPorts.map((p) => ({ ...p, count: Math.round(p.count * mul) })),
    [mul],
  );

  const liveCountryData = useMemo(() => {
    if (!geo || geo.length === 0) return null;
    return geo
      .filter((g) => g.country)
      .map((g) => ({ country: g.country, attacks: g.count }))
      .slice(0, 10);
  }, [geo]);

  const countryData = useMemo(
    () =>
      (liveCountryData ?? countriesByAttacks).map((c) => ({
        ...c,
        attacks: Math.round(c.attacks * mul),
      })),
    [liveCountryData, mul],
  );

  const filteredHourData = useMemo(() => {
    if (bucket === 'attacks') {
      return hourData.map((d) => ({ ...d, blocked: 0 }));
    }
    if (bucket === 'blocked') {
      return hourData.map((d) => ({ ...d, attacks: 0 }));
    }
    return hourData;
  }, [hourData, bucket]);

  const protocolData = useMemo(
    () => topProtocols.map((p) => ({ ...p, value: Math.round(p.value * mul) })),
    [mul],
  );

  const osData = useMemo(
    () => osDetected.map((o) => ({ ...o, value: Math.round(o.value * mul) })),
    [mul],
  );

  function exportCsv() {
    const rows = ['hour,attacks,blocked', ...filteredHourData.map((d) => `${d.hour},${d.attacks},${d.blocked}`)];
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `honeyshield-analytics-${range}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section id="analytics" className="container py-12 md:py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.5 }}
        className="mb-6"
      >
        <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-[#00BFFF]/40 bg-[#00BFFF]/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-[#00BFFF]">
          <span className="h-1.5 w-1.5 animate-pulse-glow rounded-full bg-[#00FF88]" />
          Telemetry
        </div>
        <h2 className="font-display text-2xl font-semibold tracking-tight text-[#E6F1FF] md:text-3xl">
          Attack Analytics
        </h2>
        <p className="mt-1 text-sm text-[#8A9BB8]">
          Realtime visualizations across protocols, ports, geography and operating systems.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-1 rounded-lg border border-[#1F2A44] bg-[#0B0F19] p-1">
            {(['1h', '24h', '7d', '30d'] as Range[]).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={
                  'rounded-md px-3 py-1 text-xs font-medium transition ' +
                  (range === r
                    ? 'bg-[#00BFFF] text-[#03070F] shadow-[0_0_12px_rgba(0,191,255,0.5)]'
                    : 'text-[#8A9BB8] hover:text-[#E6F1FF]')
                }
              >
                {r.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="inline-flex items-center gap-1 rounded-lg border border-[#1F2A44] bg-[#0B0F19] p-1">
            {(['all', 'attacks', 'blocked'] as Array<typeof bucket>).map((b) => (
              <button
                key={b}
                onClick={() => setBucket(b)}
                className={
                  'rounded-md px-3 py-1 text-xs font-medium capitalize transition ' +
                  (bucket === b
                    ? 'bg-[#00FF88] text-[#03070F] shadow-[0_0_12px_rgba(0,255,136,0.45)]'
                    : 'text-[#8A9BB8] hover:text-[#E6F1FF]')
                }
              >
                {b}
              </button>
            ))}
          </div>
          <Button variant="outline" size="sm" onClick={exportCsv} className="border-[#00BFFF]/40 text-[#00E5FF] hover:bg-[#00BFFF]/10">
            <Download className="mr-1.5 h-3.5 w-3.5" />
            Export CSV
          </Button>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-[#8A9BB8]">
            <FileBarChart className="h-3.5 w-3.5 text-[#00E5FF]" />
            <span>
              Showing data for {range.toUpperCase()} window
              {analytics && !usingMock ? ' · live' : ' · demo'}
            </span>
          </span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <AnalyticsCard
          title="Attacks per Hour"
          description={`${range.toUpperCase()} volume vs. blocked attempts`}
          icon={Activity}
          delay={0.05}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredHourData}>
              <defs>
                <linearGradient id="g-attacks" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00BFFF" stopOpacity={0.6} />
                  <stop offset="100%" stopColor="#00BFFF" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="g-blocked" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00FF88" stopOpacity={0.55} />
                  <stop offset="100%" stopColor="#00FF88" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1F2A44" strokeDasharray="3 3" />
              <XAxis dataKey="hour" stroke="#8A9BB8" fontSize={11} />
              <YAxis stroke="#8A9BB8" fontSize={11} />
              <Tooltip {...tooltipStyle} />
              <Area
                type="monotone"
                dataKey="attacks"
                stroke="#00BFFF"
                strokeWidth={2}
                fill="url(#g-attacks)"
                animationDuration={1400}
              />
              <Area
                type="monotone"
                dataKey="blocked"
                stroke="#00FF88"
                strokeWidth={2}
                fill="url(#g-blocked)"
                animationDuration={1400}
              />
            </AreaChart>
          </ResponsiveContainer>
        </AnalyticsCard>

        <AnalyticsCard
          title="Top Protocols"
          description="Distribution of attack traffic by service"
          icon={Network}
          delay={0.1}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={protocolData}
                dataKey="value"
                nameKey="name"
                innerRadius={56}
                outerRadius={95}
                stroke="#0B0F19"
                strokeWidth={3}
                animationDuration={1200}
              >
                {topProtocols.map((p, i) => (
                  <Cell key={i} fill={p.color} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend
                wrapperStyle={{ fontSize: 11, color: '#8A9BB8' }}
                iconType="circle"
              />
            </PieChart>
          </ResponsiveContainer>
        </AnalyticsCard>

        <AnalyticsCard
          title="Most Targeted Ports"
          description="Destination ports hit in the last hour"
          icon={Server}
          delay={0.15}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={portData}>
              <CartesianGrid stroke="#1F2A44" strokeDasharray="3 3" />
              <XAxis dataKey="port" stroke="#8A9BB8" fontSize={10} interval={0} angle={-15} dy={6} />
              <YAxis stroke="#8A9BB8" fontSize={11} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]} animationDuration={1400}>
                {portData.map((_, i) => (
                  <Cell key={i} fill={i % 2 === 0 ? '#00BFFF' : '#00FF88'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </AnalyticsCard>

        <AnalyticsCard
          title="Countries by Attack Count"
          description="Top 10 sources ranked"
          icon={Globe}
          delay={0.2}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={countryData} layout="vertical">
              <CartesianGrid stroke="#1F2A44" strokeDasharray="3 3" />
              <XAxis type="number" stroke="#8A9BB8" fontSize={11} />
              <YAxis dataKey="country" type="category" stroke="#8A9BB8" fontSize={11} width={100} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="attacks" fill="#00E5FF" radius={[0, 6, 6, 0]} animationDuration={1400} />
            </BarChart>
          </ResponsiveContainer>
        </AnalyticsCard>

        <AnalyticsCard
          title="Operating Systems Detected"
          description="Fingerprints from captured banners"
          icon={Shield}
          delay={0.25}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={osData}
                dataKey="value"
                nameKey="name"
                outerRadius={95}
                stroke="#0B0F19"
                strokeWidth={3}
                animationDuration={1200}
              >
                {osDetected.map((_, i) => (
                  <Cell
                    key={i}
                    fill={['#00BFFF', '#00E5FF', '#00FF88', '#FFD600', '#FF8A1F', '#FF3D6E'][i % 6]}
                  />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#8A9BB8' }} iconType="circle" />
            </PieChart>
          </ResponsiveContainer>
        </AnalyticsCard>

        <AnalyticsCard
          title="Attack Distribution"
          description="Detected vs. blocked vs. successful"
          icon={TrendingUp}
          delay={0.3}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={filteredHourData.map((d, i) => ({
                hour: d.hour,
                unique: d.unique + i * 12,
                blocked: d.blocked - i * 8,
              }))}
            >
              <CartesianGrid stroke="#1F2A44" strokeDasharray="3 3" />
              <XAxis dataKey="hour" stroke="#8A9BB8" fontSize={11} />
              <YAxis stroke="#8A9BB8" fontSize={11} />
              <Tooltip {...tooltipStyle} />
              <Line
                type="monotone"
                dataKey="unique"
                stroke="#00BFFF"
                strokeWidth={2}
                dot={false}
                animationDuration={1500}
              />
              <Line
                type="monotone"
                dataKey="blocked"
                stroke="#00FF88"
                strokeWidth={2}
                dot={false}
                animationDuration={1500}
              />
            </LineChart>
          </ResponsiveContainer>
        </AnalyticsCard>
      </div>
    </section>
  );
}