import { motion } from 'framer-motion';
import { ArrowDown, ArrowUp, Bot, Bug, ExternalLink, ShieldAlert, Skull, Target } from 'lucide-react';
import { useMemo, useState } from 'react';
import { malwareFamilies, mitre, recentCVEs, severityColor, type Severity } from '../lib/mock-data';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { SectionHeader } from '../components/fx/SectionHeader';

function MalwareCard({
  m,
  index,
}: {
  m: (typeof malwareFamilies)[number];
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ delay: index * 0.06, duration: 0.5 }}
    >
      <Card className="group h-full overflow-hidden p-0">
        <div className="relative overflow-hidden p-5">
          <div
            className="absolute inset-0 opacity-20"
            style={{ background: `radial-gradient(circle at 80% 20%, ${severityColor(m.severity)}, transparent 60%)` }}
          />
          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span
                className="grid h-10 w-10 place-items-center rounded-md border"
                style={{
                  borderColor: severityColor(m.severity) + '60',
                  background: severityColor(m.severity) + '15',
                  color: severityColor(m.severity),
                }}
              >
                <Skull className="h-4 w-4" />
              </span>
              <div>
                <p className="font-display text-base font-semibold text-[#E6F1FF]">{m.name}</p>
                <p className="text-xs text-[#8A9BB8]">{m.tag}</p>
              </div>
            </div>
            <Badge variant={m.severity === 'critical' ? 'danger' : 'warning'}>{m.severity}</Badge>
          </div>
          <p className="relative mt-3 text-xs text-[#8A9BB8]">{m.description}</p>
        </div>
        <div className="border-t border-[#1F2A44] bg-[#0B0F19]/60 px-5 py-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#8A9BB8]">Detections</span>
            <span className="font-mono text-[#E6F1FF]">{m.detections.toLocaleString()}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className="text-[#8A9BB8]">Trend</span>
            <span className={m.growth.startsWith('-') ? 'text-[#00FF88]' : 'text-[#FF3D6E]'}>
              {m.growth}
            </span>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function CVECard({ cve, index }: { cve: (typeof recentCVEs)[number]; index: number }) {
  const tone = cve.cvss >= 9.5 ? 'danger' : cve.cvss >= 8.5 ? 'warning' : 'default';
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
    >
      <Card className="h-full p-4 hover:border-[#00BFFF]/50">
        <div className="flex items-center justify-between">
          <code className="font-mono text-xs text-[#00E5FF]">{cve.id}</code>
          <Badge variant={tone}>{cve.cvss} CVSS</Badge>
        </div>
        <p className="mt-2 text-sm font-semibold text-[#E6F1FF]">{cve.title}</p>
        <div className="mt-3 flex items-center justify-between text-xs">
          <span className={cve.exploited ? 'text-[#FF3D6E]' : 'text-[#00FF88]'}>
            {cve.exploited ? '⚠ Exploited in the wild' : 'Not exploited'}
          </span>
          <a className="flex items-center gap-1 text-[#00BFFF] hover:underline" href="#">
            Details <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </Card>
    </motion.div>
  );
}

export function ThreatIntel() {
  const [severityFilter, setSeverityFilter] = useState<'all' | Severity>('all');
  const [cveSort, setCveSort] = useState<'desc' | 'asc'>('desc');
  const [cveExploitedOnly, setCveExploitedOnly] = useState(false);
  const [mitreSort, setMitreSort] = useState<'desc' | 'asc'>('desc');

  const filteredMalware = useMemo(
    () =>
      severityFilter === 'all'
        ? malwareFamilies
        : malwareFamilies.filter((m) => m.severity === severityFilter),
    [severityFilter],
  );

  const sortedCVEs = useMemo(() => {
    const list = cveExploitedOnly ? recentCVEs.filter((c) => c.exploited) : recentCVEs;
    return [...list].sort((a, b) => (cveSort === 'desc' ? b.cvss - a.cvss : a.cvss - b.cvss));
  }, [cveSort, cveExploitedOnly]);

  const sortedMitre = useMemo(
    () => [...mitre].sort((a, b) => (mitreSort === 'desc' ? b.count - a.count : a.count - b.count)),
    [mitreSort],
  );

  const totalMitre = sortedMitre.reduce((s, m) => s + m.count, 0);

  const severityOptions: Array<'all' | Severity> = ['all', 'critical', 'high', 'medium', 'low'];

  return (
    <section id="intel" className="container py-12 md:py-16">
      <SectionHeader
        eyebrow="Threat Intelligence"
        title="Active Malware & CVEs"
        subtitle="Curated indicators from the honeypot mesh, MITRE ATT&CK mapping, and NVD feed."
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h3 className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-[#8A9BB8]">
              <Bug className="h-3.5 w-3.5 text-[#FF3D6E]" /> Latest Malware Families
            </h3>
            <div className="inline-flex items-center gap-1 rounded-lg border border-[#1F2A44] bg-[#0B0F19] p-1">
              {severityOptions.map((s) => (
                <button
                  key={s}
                  onClick={() => setSeverityFilter(s)}
                  className={
                    'rounded-md px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider transition ' +
                    (severityFilter === s
                      ? 'bg-[#00BFFF] text-[#03070F] shadow-[0_0_10px_rgba(0,191,255,0.5)]'
                      : 'text-[#8A9BB8] hover:text-[#E6F1FF]')
                  }
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {filteredMalware.length === 0 ? (
              <div className="col-span-full rounded-md border border-dashed border-[#1F2A44] bg-[#0B0F19]/40 p-6 text-center text-xs text-[#8A9BB8]">
                No malware families match the {severityFilter} severity filter.
              </div>
            ) : (
              filteredMalware.map((m, i) => <MalwareCard key={m.name} m={m} index={i} />)
            )}
          </div>
        </div>

        <div>
          <h3 className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-[#8A9BB8]">
            <Bot className="h-3.5 w-3.5 text-[#FFD600]" /> Botnet Activity
          </h3>
          <Card>
            <CardHeader>
              <CardTitle>Network Risk Score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {[
                { label: 'Overall', value: 78, color: 'orange' as const, tone: '#FF8A1F' },
                { label: 'Mirai Family', value: 92, color: 'red' as const, tone: '#FF3D6E' },
                { label: 'P2P Botnets', value: 64, color: 'orange' as const, tone: '#FFD600' },
                { label: 'Unknown', value: 28, color: 'green' as const, tone: '#00FF88' },
              ].map((s) => (
                <div key={s.label}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[#E6F1FF]">{s.label}</span>
                    <span className="font-mono" style={{ color: s.tone }}>
                      {s.value} / 100
                    </span>
                  </div>
                  <Progress value={s.value} tone={s.color} />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h3 className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-[#8A9BB8]">
              <ShieldAlert className="h-3.5 w-3.5 text-[#00BFFF]" /> Top Exploited CVEs
            </h3>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCveExploitedOnly((v) => !v)}
                className={
                  'border-[#FF3D6E]/40 text-xs ' +
                  (cveExploitedOnly ? 'bg-[#FF3D6E]/15 text-[#FF3D6E]' : 'text-[#8A9BB8]')
                }
              >
                {cveExploitedOnly ? 'Exploited only ✓' : 'Show exploited only'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCveSort((v) => (v === 'desc' ? 'asc' : 'desc'))}
                className="border-[#00BFFF]/40 text-xs text-[#00E5FF]"
              >
                {cveSort === 'desc' ? (
                  <ArrowDown className="mr-1 h-3 w-3" />
                ) : (
                  <ArrowUp className="mr-1 h-3 w-3" />
                )}
                CVSS {cveSort === 'desc' ? 'high→low' : 'low→high'}
              </Button>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {sortedCVEs.length === 0 ? (
              <div className="col-span-full rounded-md border border-dashed border-[#1F2A44] bg-[#0B0F19]/40 p-6 text-center text-xs text-[#8A9BB8]">
                No CVEs match the active filter.
              </div>
            ) : (
              sortedCVEs.map((c, i) => <CVECard key={c.id} cve={c} index={i} />)
            )}
          </div>
        </div>

        <div>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-[#8A9BB8]">
              <Target className="h-3.5 w-3.5 text-[#00E5FF]" /> MITRE ATT&CK
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMitreSort((v) => (v === 'desc' ? 'asc' : 'desc'))}
              className="border-[#00BFFF]/40 text-[10px] text-[#00E5FF]"
            >
              {mitreSort === 'desc' ? (
                <ArrowDown className="mr-1 h-3 w-3" />
              ) : (
                <ArrowUp className="mr-1 h-3 w-3" />
              )}
              Count
            </Button>
          </div>
          <Card className="p-0">
            <ul className="divide-y divide-[#1F2A44]">
              {sortedMitre.map((m) => {
                const pct = Math.round((m.count / totalMitre) * 100);
                return (
                  <li key={m.id} className="flex items-center gap-3 px-4 py-3">
                    <code className="font-mono text-xs text-[#00E5FF]">{m.id}</code>
                    <div className="flex-1">
                      <div className="flex items-center justify-between text-xs text-[#E6F1FF]">
                        <span>{m.name}</span>
                        <span className="text-[#8A9BB8]">{m.count.toLocaleString()}</span>
                      </div>
                      <Progress value={pct * 4} tone="cyan" />
                    </div>
                  </li>
                );
              })}
            </ul>
          </Card>
        </div>
      </div>
    </section>
  );
}