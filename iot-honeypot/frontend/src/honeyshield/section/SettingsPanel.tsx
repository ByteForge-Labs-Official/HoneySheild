import { motion } from 'framer-motion';
import { Bell, Download, KeyRound, Mail, MessageCircle, Slack, Webhook } from 'lucide-react';
import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { SectionHeader } from '../components/fx/SectionHeader';

export function SettingsPanel() {
  const [prefs, setPrefs] = useState({
    sound: true,
    desktop: true,
    email: false,
    telegram: true,
    slack: false,
    webhook: true,
  });

  return (
    <section id="settings" className="container py-12 md:py-16">
      <SectionHeader
        eyebrow="Configuration"
        title="Settings"
        subtitle="Tune alerts, API integrations, and data exports for your SOC."
      />
      <Tabs defaultValue="notifications">
        <TabsList>
          <TabsTrigger value="notifications">
            <Bell className="mr-1 h-3.5 w-3.5" /> Notifications
          </TabsTrigger>
          <TabsTrigger value="api">
            <KeyRound className="mr-1 h-3.5 w-3.5" /> API Keys
          </TabsTrigger>
          <TabsTrigger value="webhooks">
            <Webhook className="mr-1 h-3.5 w-3.5" /> Webhooks
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Mail className="mr-1 h-3.5 w-3.5" /> Alerts
          </TabsTrigger>
          <TabsTrigger value="export">
            <Download className="mr-1 h-3.5 w-3.5" /> Export
          </TabsTrigger>
        </TabsList>

        <TabsContent value="notifications">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>How HoneyShield AI should reach you.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { k: 'sound', label: 'Sound alerts on critical events' },
                  { k: 'desktop', label: 'Desktop notifications' },
                  { k: 'email', label: 'Email digests (daily summary)' },
                  { k: 'telegram', label: 'Telegram alerts' },
                  { k: 'slack', label: 'Slack alerts' },
                  { k: 'webhook', label: 'Generic webhook' },
                ].map((row) => (
                  <div
                    key={row.k}
                    className="flex items-center justify-between rounded-md border border-[#1F2A44] bg-[#0B0F19]/40 px-4 py-3"
                  >
                    <span className="text-sm text-[#E6F1FF]">{row.label}</span>
                    <Switch
                      checked={prefs[row.k as keyof typeof prefs]}
                      onCheckedChange={(v) => setPrefs((p) => ({ ...p, [row.k]: v }))}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        <TabsContent value="api">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle>API Keys</CardTitle>
                <CardDescription>Programmatic access for your SIEM and scripts.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <ApiKeyRow name="SOC Streaming" prefix="hs_live_4f9a" />
                <ApiKeyRow name="Threat Intel Pull" prefix="hs_live_8d2c" />
                <ApiKeyRow name="Webhook Signing" prefix="hs_live_0a31" />
                <Button variant="outline" size="sm">
                  <KeyRound className="h-3.5 w-3.5" /> Generate new key
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        <TabsContent value="webhooks">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle>Webhook Integrations</CardTitle>
                <CardDescription>Forward attack events to your downstream tooling.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-2 md:grid-cols-[1fr_180px_auto]">
                  <Input placeholder="https://your-webhook.example/honeyshield" />
                  <select className="h-10 rounded-md border border-[#1F2A44] bg-[#0F1626]/80 px-3 text-sm text-[#E6F1FF]">
                    <option>events:all</option>
                    <option>events:critical</option>
                    <option>events:honeypot</option>
                  </select>
                  <Button>Add Webhook</Button>
                </div>
                {[
                  { url: 'https://hooks.slack.com/services/T000/B000/honeyshield', events: 'critical' },
                  { url: 'https://siem.acme.local/v1/honeypot', events: 'all' },
                ].map((w) => (
                  <div
                    key={w.url}
                    className="flex items-center justify-between rounded-md border border-[#1F2A44] bg-[#0B0F19]/40 px-4 py-2.5 font-mono text-xs"
                  >
                    <span className="truncate text-[#E6F1FF]">{w.url}</span>
                    <span className="ml-2 text-[#8A9BB8]">{w.events}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        <TabsContent value="alerts">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle>Alert Channels</CardTitle>
                <CardDescription>Configure delivery destinations.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-3">
                {[
                  { icon: Mail, label: 'Email', placeholder: 'soc@acme.com' },
                  { icon: MessageCircle, label: 'Telegram', placeholder: '@honeyshield_bot' },
                  { icon: Slack, label: 'Slack', placeholder: '#soc-alerts' },
                ].map((row) => (
                  <div
                    key={row.label}
                    className="rounded-md border border-[#1F2A44] bg-[#0B0F19]/40 p-4"
                  >
                    <div className="mb-2 flex items-center gap-2 text-sm text-[#E6F1FF]">
                      <row.icon className="h-4 w-4 text-[#00BFFF]" /> {row.label}
                    </div>
                    <Input placeholder={row.placeholder} />
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        <TabsContent value="export">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle>Export Data</CardTitle>
                <CardDescription>Download events for forensic analysis.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <Button variant="outline">
                  <Download className="h-3.5 w-3.5" /> Export CSV (24h)
                </Button>
                <Button variant="outline">
                  <Download className="h-3.5 w-3.5" /> Export JSON (7d)
                </Button>
                <Button variant="outline">
                  <Download className="h-3.5 w-3.5" /> PCAP Bundle
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>
      </Tabs>
    </section>
  );
}

function ApiKeyRow({ name, prefix }: { name: string; prefix: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-[#1F2A44] bg-[#0B0F19]/40 px-4 py-3">
      <div>
        <p className="text-sm font-medium text-[#E6F1FF]">{name}</p>
        <code className="font-mono text-xs text-[#8A9BB8]">{prefix}••••••••••••••</code>
      </div>
      <Button variant="ghost" size="sm">
        Reveal
      </Button>
    </div>
  );
}