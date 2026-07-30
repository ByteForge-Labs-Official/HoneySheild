import { motion } from 'framer-motion';
import { Bell, Database, Hexagon, LogIn, LogOut, Palette, Shield, ShieldAlert, UserCog } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { BackgroundFX } from '../components/fx/BackgroundFX';
import { Footer } from '../components/layout/Footer';
import { SettingsPanel } from '../section/SettingsPanel';

function SettingsHeader() {
  const navigate = useNavigate();
  const [authed, setAuthed] = useState(false);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const sync = () => {
      setAuthed(Boolean(window.localStorage.getItem('hs_access_token')));
      setEmail(window.localStorage.getItem('hs_user_email'));
    };
    sync();
    window.addEventListener('storage', sync);
    window.addEventListener('hs:auth', sync);
    return () => {
      window.removeEventListener('storage', sync);
      window.removeEventListener('hs:auth', sync);
    };
  }, []);

  function signOut() {
    window.localStorage.removeItem('hs_access_token');
    window.localStorage.removeItem('hs_user_email');
    window.dispatchEvent(new Event('hs:auth'));
    setAuthed(false);
    navigate('/login');
  }

  return (
    <header className="sticky top-0 z-40 border-b border-[#1F2A44]/80 bg-[#0B0F19]/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center gap-6">
        <Link
          to="/"
          className="flex items-center gap-2.5"
          aria-label="HoneyShield AI home"
        >
          <span className="relative grid h-9 w-9 place-items-center rounded-lg border border-[#00BFFF]/40 bg-gradient-to-br from-[#00BFFF]/20 to-[#00FF88]/10 shadow-[0_0_18px_rgba(0,191,255,0.35)]">
            <Hexagon className="h-5 w-5 text-[#00E5FF]" strokeWidth={2.2} />
            <Shield className="absolute h-3.5 w-3.5 text-[#00FF88]" strokeWidth={2.4} />
          </span>
          <span className="flex flex-col leading-tight">
            <span className="font-display text-sm font-semibold tracking-wide text-[#E6F1FF]">
              HoneyShield <span className="neon-text">AI</span>
            </span>
            <span className="text-[10px] uppercase tracking-[0.18em] text-[#8A9BB8]">
              Settings
            </span>
          </span>
        </Link>
        <nav className="ml-auto flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => navigate('/')}>
            Back to dashboard
          </Button>
          {authed ? (
            <Button variant="ghost" size="icon" onClick={signOut} aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          ) : (
            <Button size="sm" onClick={() => navigate('/login')}>
              <LogIn className="mr-1.5 h-3.5 w-3.5" /> Sign in
            </Button>
          )}
        </nav>
      </div>
    </header>
  );
}

export function SettingsPage() {
  const [profile, setProfile] = useState({
    name: 'Analyst Athena',
    role: 'SOC T2',
    timezone: 'UTC+1 · Berlin',
    siem: 'Elastic 8.14',
  });
  const [dangerArmed, setDangerArmed] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'pcap'>('json');

  return (
    <div className="relative min-h-screen text-[#E6F1FF]">
      <BackgroundFX />
      <SettingsHeader />

      <main className="container py-10 md:py-14">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"
        >
          <div>
            <Badge variant="default" className="uppercase tracking-[0.32em]">
              <Bell className="mr-1.5 h-3 w-3" /> Configuration
            </Badge>
            <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
              <span className="bg-gradient-to-r from-[#00BFFF] via-[#00E5FF] to-[#00FF88] bg-clip-text text-transparent">
                Workspace settings
              </span>
            </h1>
            <p className="mt-2 max-w-xl text-sm text-[#8A9BB8]">
              Tune your SOC profile, alert routing, integrations, data exports, and the
              HoneyShield appearance. All changes persist locally and push to the
              backend on save.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary">Reset to defaults</Button>
            <Button>Save changes</Button>
          </div>
        </motion.div>

        <Tabs defaultValue="profile" className="mt-8">
          <TabsList className="flex-wrap">
            <TabsTrigger value="profile">
              <UserCog className="mr-1 h-3.5 w-3.5" /> Profile
            </TabsTrigger>
            <TabsTrigger value="notifications">
              <Bell className="mr-1 h-3.5 w-3.5" /> Notifications
            </TabsTrigger>
            <TabsTrigger value="branding">
              <Palette className="mr-1 h-3.5 w-3.5" /> Branding
            </TabsTrigger>
            <TabsTrigger value="data">
              <Database className="mr-1 h-3.5 w-3.5" /> Data &amp; Export
            </TabsTrigger>
            <TabsTrigger value="danger">
              <ShieldAlert className="mr-1 h-3.5 w-3.5" /> Danger zone
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardHeader>
                  <CardTitle>Analyst profile</CardTitle>
                  <CardDescription>
                    Who is operating this HoneyShield console.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  {([
                    {
                      k: 'name',
                      label: 'Display name',
                      placeholder: 'Athena',
                    },
                    {
                      k: 'role',
                      label: 'Role / tier',
                      placeholder: 'SOC T2',
                    },
                    {
                      k: 'timezone',
                      label: 'Time zone',
                      placeholder: 'UTC+1 · Berlin',
                    },
                    {
                      k: 'siem',
                      label: 'Default SIEM',
                      placeholder: 'Elastic 8.14',
                    },
                  ] as const).map((f) => (
                    <label key={f.k} className="block">
                      <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                        {f.label}
                      </span>
                      <Input
                        className="mt-1"
                        value={profile[f.k]}
                        placeholder={f.placeholder}
                        onChange={(e) =>
                          setProfile((p) => ({ ...p, [f.k]: e.target.value }))
                        }
                      />
                    </label>
                  ))}
                  <div className="md:col-span-2 flex items-center justify-between rounded-md border border-[#1F2937] bg-[#0A0F1A]/40 px-4 py-3">
                    <div>
                      <p className="text-sm text-[#E6F1FF]">Quiet hours</p>
                      <p className="text-xs text-[#8A9BB8]">
                        Mute non-critical alerts between 22:00–07:00 local time.
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          <TabsContent value="notifications">
            {/* Reuse existing notifications/api/webhooks/alerts/export panel */}
            <SettingsPanel />
          </TabsContent>

          <TabsContent value="branding">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Console appearance</CardTitle>
                    <CardDescription>Pick the colour tone across surfaces.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {[
                      { c: 'from-[#00BFFF] to-[#00E5FF]', label: 'Cyan mesh' },
                      { c: 'from-[#FF3D6E] to-[#00BFFF]', label: 'Alert' },
                      { c: 'from-[#00FF88] to-[#00BFFF]', label: 'Calm' },
                      { c: 'from-[#A78BFA] to-[#00E5FF]', label: 'Aurora' },
                    ].map((t) => (
                      <button
                        type="button"
                        key={t.label}
                        className="flex w-full items-center justify-between rounded-md border border-[#1F2937] bg-[#0A0F1A]/40 px-3 py-2 text-left transition hover:border-[#00BFFF]/50"
                      >
                        <span className="flex items-center gap-3">
                          <span
                            className={`inline-block h-6 w-12 rounded bg-gradient-to-r ${t.c}`}
                          />
                          <span className="text-sm text-[#E6F1FF]">{t.label}</span>
                        </span>
                        <Badge variant="outline">Default</Badge>
                      </button>
                    ))}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Workspace identity</CardTitle>
                    <CardDescription>
                      Logo &amp; naming on shared exports.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <label className="block">
                      <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                        Workspace name
                      </span>
                      <Input className="mt-1" defaultValue="HoneyShield · Berlin Mesh" />
                    </label>
                    <label className="block">
                      <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                        Logo URL
                      </span>
                      <Input
                        className="mt-1"
                        placeholder="https://cdn.honeyshield.io/logo.svg"
                      />
                    </label>
                    <label className="block">
                      <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                        Subdomain
                      </span>
                      <Input className="mt-1" defaultValue="berlin.honeyshield.io" />
                    </label>
                  </CardContent>
                </Card>
              </div>
            </motion.div>
          </TabsContent>

          <TabsContent value="data">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardHeader>
                  <CardTitle>Data retention &amp; exports</CardTitle>
                  <CardDescription>
                    Choose what stays in the mesh and how it leaves.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    {(['json', 'csv', 'pcap'] as const).map((f) => (
                      <button
                        key={f}
                        type="button"
                        onClick={() => setExportFormat(f)}
                        className={`rounded-md border px-3 py-3 text-left text-sm transition ${
                          exportFormat === f
                            ? 'border-[#00BFFF]/60 bg-[#00BFFF]/10 text-[#E6F1FF]'
                            : 'border-[#1F2937] bg-[#0A0F1A]/40 text-[#8A9BB8] hover:border-[#00BFFF]/40'
                        }`}
                      >
                        <p className="font-semibold uppercase tracking-[0.2em]">{f}</p>
                        <p className="mt-1 text-[11px] text-[#8A9BB8]">
                          {f === 'json' && 'Structured events, ideal for SIEMs.'}
                          {f === 'csv' && 'Spreadsheet-friendly summaries.'}
                          {f === 'pcap' && 'Full packet captures for forensics.'}
                        </p>
                      </button>
                    ))}
                  </div>
                  {[
                    { label: 'Keep raw events', d: '30 days' },
                    { label: 'Keep aggregated stats', d: '2 years' },
                    { label: 'PCAP archive', d: '7 days cold storage' },
                  ].map((row) => (
                    <div
                      key={row.label}
                      className="flex items-center justify-between rounded-md border border-[#1F2937] bg-[#0A0F1A]/40 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm text-[#E6F1FF]">{row.label}</p>
                        <p className="text-xs text-[#8A9BB8]">{row.d}</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  ))}
                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button>
                      <Database className="mr-2 h-4 w-4" /> Export {exportFormat.toUpperCase()}
                    </Button>
                    <Button variant="secondary">Schedule a recurring export</Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          <TabsContent value="danger">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="border-[#FF3D6E]/40">
                <CardHeader>
                  <CardTitle className="text-[#FF6F8F]">Danger zone</CardTitle>
                  <CardDescription>
                    Destructive actions. Proceed carefully — these cannot be undone.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between rounded-md border border-[#FF3D6E]/40 bg-[#FF3D6E]/5 px-4 py-3">
                    <div>
                      <p className="text-sm text-[#E6F1FF]">Rotate all API keys</p>
                      <p className="text-xs text-[#8A9BB8]">
                        Invalidates every active integration token.
                      </p>
                    </div>
                    <Button variant="secondary">Rotate</Button>
                  </div>
                  <div className="flex items-center justify-between rounded-md border border-[#FF3D6E]/40 bg-[#FF3D6E]/5 px-4 py-3">
                    <div>
                      <p className="text-sm text-[#E6F1FF]">Reset honeypot fleet</p>
                      <p className="text-xs text-[#8A9BB8]">
                        Rebuilt all honeypot profiles from default blueprints.
                      </p>
                    </div>
                    <Button variant="secondary">Reset</Button>
                  </div>
                  <div className="rounded-md border border-[#FF3D6E]/40 bg-[#FF3D6E]/5 px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[#E6F1FF]">Tear down workspace</p>
                        <p className="text-xs text-[#8A9BB8]">
                          Drops the database, cache, and exports. Permanent.
                        </p>
                      </div>
                      <Switch
                        checked={dangerArmed}
                        onCheckedChange={setDangerArmed}
                      />
                    </div>
                    <div className="mt-3 flex items-center justify-end gap-2">
                      <Button variant="ghost">Cancel</Button>
                      <Button disabled={!dangerArmed} variant="danger">
                        Confirm teardown
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>
        </Tabs>
      </main>

      <Footer />
    </div>
  );
}

export default SettingsPage;
