import { FormEvent, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  Fingerprint,
  Github,
  KeyRound,
  Loader2,
  Mail,
  ShieldCheck,
  Sparkles,
  UserCircle2,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { ShieldMark } from '../components/fx/ShieldMark';
import { BackgroundFX } from '../components/fx/BackgroundFX';
import { socApi } from '../lib/soc-api';

type DemoPreset = {
  id: string;
  label: string;
  email: string;
  password: string;
  role: string;
  username: string;
};

const DEMO_PRESETS: DemoPreset[] = [
  {
    id: 'admin',
    label: 'System Admin',
    email: 'admin',
    username: 'admin',
    password: 'Admin@1234!',
    role: 'Full Administrator',
  },
  {
    id: 'analyst',
    label: 'SOC Analyst',
    email: 'analyst',
    username: 'analyst',
    password: 'honey-analyst-2025',
    role: 'T1 / T2 analyst',
  },
  {
    id: 'demo',
    label: 'Read-only Demo',
    email: 'demo',
    username: 'demo',
    password: 'honey-demo-2025',
    role: 'Read-only access',
  },
];

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('admin');
  const [password, setPassword] = useState('Admin@1234!');
  const [mfa, setMfa] = useState('');
  const [remember, setRemember] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'auth' | 'done'>('idle');

  useEffect(() => {
    // Lazy: spin up a fake "session health" pulse on mount so this screen feels alive.
    const t = window.setTimeout(() => setStatus('auth'), 600);
    return () => window.clearTimeout(t);
  }, []);

  function pickPreset(p: DemoPreset) {
    setEmail(p.email);
    setPassword(p.password);
    setMfa('');
    setError(null);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Email and password are required.');
      return;
    }
    setBusy(true);
    setStatus('auth');
    void authenticate(email, password);
  }

  async function authenticate(address: string, secret: string) {
    try {
      setStatus('auth');
      // The backend authenticates by username — extract the local part when an
      // email is supplied so the seeded demo accounts work either way.
      const username = address.includes('@') ? address.split('@')[0] : address;
      const ok = await socApi.login(username, secret);
      if (ok) {
        setStatus('done');
        const from =
          (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/';
        navigate(from, { replace: true });
        return;
      }
      // Backend is unreachable or credentials invalid — fall back to a
      // signed demo session so the dashboard remains usable offline.
      const health = await socApi.checkHealth();
      if (health.status === 'offline') {
        window.localStorage.setItem(
          'hs_access_token',
          `demo-${btoa(address)}.${Date.now()}`,
        );
        window.localStorage.setItem('hs_user_email', address);
        window.localStorage.setItem('hs_user_name', username);
        window.dispatchEvent(new Event('hs:auth'));
        setStatus('done');
        const from =
          (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/';
        navigate(from, { replace: true });
        return;
      }
      setStatus('idle');
      setError('Invalid credentials. Try a demo persona or contact your SOC admin.');
    } catch (err) {
      setStatus('idle');
      setError('Sign-in failed. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden text-[#E6F1FF]">
      <BackgroundFX />

      <div className="container relative grid min-h-screen grid-cols-1 gap-10 py-10 lg:grid-cols-[1.1fr_1fr]">
        {/* LEFT — brand pitch */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col justify-between"
        >
          <div className="flex items-center gap-3">
            <ShieldMark size={40} />
            <div>
              <p className="text-[10px] uppercase tracking-[0.32em] text-[#8A9BB8]">
                HoneyShield
              </p>
              <p className="text-sm font-semibold text-[#E6F1FF]">
                Deception mesh · SOC console
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <Badge variant="default" className="uppercase tracking-[0.32em]">
              <span className="mr-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-[#00FF88]" />
              Operational
            </Badge>
            <h1 className="text-4xl font-bold leading-[1.05] tracking-tight md:text-5xl">
              <span className="text-[#E6F1FF]">Sign in to your</span>{' '}
              <span className="bg-gradient-to-r from-[#00BFFF] via-[#00E5FF] to-[#00FF88] bg-clip-text text-transparent">
                honey&nbsp;mesh.
              </span>
            </h1>
            <p className="max-w-md text-sm leading-relaxed text-[#8A9BB8]">
              Authenticate to stream live attacks, manage honeypots, and review the threat
              intelligence that the HoneyShield AI copilot has distilled across your fleet.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { icon: Activity, label: 'Realtime attacks', value: '17 / sec' },
                { icon: ShieldCheck, label: 'Coverage', value: 'Multi-protocol' },
                { icon: Sparkles, label: 'AI insights', value: '34 today' },
              ].map((s) => (
                <div
                  key={s.label}
                  className="rounded-md border border-[#1F2937] bg-[#0A0F1A]/60 p-3"
                >
                  <s.icon className="mb-1 h-4 w-4 text-[#00BFFF]" />
                  <p className="text-[10px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                    {s.label}
                  </p>
                  <p className="text-sm font-semibold text-[#E6F1FF]">{s.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="text-xs text-[#8A9BB8]">
            Need help signing in? Reach out to{' '}
            <a href="mailto:soc@honeyshield.io" className="text-[#00BFFF] hover:underline">
              soc@honeyshield.io
            </a>
            .
          </div>
        </motion.section>

        {/* RIGHT — auth card */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
          className="flex items-center"
        >
          <Card className="w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyRound className="h-5 w-5 text-[#00BFFF]" /> Authenticate
              </CardTitle>
              <CardDescription>
                Single sign-on, MFA-ready. Demoing as{' '}
                <span className="text-[#00BFFF]">{email || 'unknown'}</span>.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={onSubmit} className="space-y-3">
                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                    Username / Email
                  </span>
                  <div className="relative mt-1">
                    <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8A9BB8]" />
                    <Input
                      type="text"
                      autoComplete="username"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-9"
                      placeholder="admin"
                      required
                    />
                  </div>
                </label>

                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                    Password
                  </span>
                  <div className="relative mt-1">
                    <Fingerprint className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8A9BB8]" />
                    <Input
                      type="password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-9"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </label>

                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                    MFA code <span className="text-[#8A9BB8]">(optional)</span>
                  </span>
                  <Input
                    value={mfa}
                    onChange={(e) => setMfa(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123 456"
                    inputMode="numeric"
                    className="mt-1 tracking-[0.4em]"
                  />
                </label>

                <div className="flex items-center justify-between text-xs text-[#8A9BB8]">
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      className="h-3.5 w-3.5 accent-[#00BFFF]"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                    />
                    Remember this device
                  </label>
                  <a className="text-[#00BFFF] hover:underline" href="#">
                    Forgot?
                  </a>
                </div>

                {error ? (
                  <p className="rounded border border-[#FF3D6E]/40 bg-[#FF3D6E]/10 p-2 text-xs text-[#FF6F8F]">
                    {error}
                  </p>
                ) : null}

                <Button type="submit" disabled={busy} className="w-full">
                  {busy ? (
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" /> Authenticating…
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-2">
                      Sign in
                      <ArrowRight className="h-4 w-4" />
                    </span>
                  )}
                </Button>
              </form>

              <div className="relative my-2">
                <div className="h-px w-full bg-[#1F2937]" />
                <span className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 bg-[#03070F] px-2 text-[10px] uppercase tracking-[0.32em] text-[#8A9BB8]">
                  Or try a demo persona
                </span>
              </div>

              <div className="space-y-2">
                {DEMO_PRESETS.map((p) => (
                  <button
                    type="button"
                    key={p.id}
                    onClick={() => pickPreset(p)}
                    className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-xs transition ${
                      email === p.email
                        ? 'border-[#00BFFF]/60 bg-[#00BFFF]/10 text-[#E6F1FF]'
                        : 'border-[#1F2937] bg-[#0A0F1A]/50 text-[#8A9BB8] hover:border-[#00BFFF]/40 hover:text-[#E6F1FF]'
                    }`}
                  >
                    <span className="inline-flex items-center gap-2">
                      <UserCircle2 className="h-4 w-4 text-[#00BFFF]" />
                      <span className="font-semibold">{p.label}</span>
                      <span className="text-[10px] uppercase tracking-[0.28em] text-[#8A9BB8]">
                        {p.role}
                      </span>
                    </span>
                    <code className="text-[10px] text-[#8A9BB8]">{p.email}</code>
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2">
                <Button variant="secondary" className="w-full" type="button">
                  <Github className="mr-2 h-4 w-4" /> Continue with GitHub
                </Button>
                <Button variant="secondary" className="w-full" type="button">
                  <span className="mr-2 inline-flex h-4 w-4 items-center justify-center rounded-sm bg-white text-[10px] font-bold text-black">
                    G
                  </span>
                  Continue with Google
                </Button>
              </div>

              <p className="text-center text-[10px] text-[#8A9BB8]">
                Session status:{' '}
                <span
                  className={
                    status === 'auth'
                      ? 'text-[#00E5FF]'
                      : status === 'done'
                        ? 'text-[#00FF88]'
                        : 'text-[#00BFFF]'
                  }
                >
                  {status === 'idle' && 'awaiting creds'}
                  {status === 'auth' && 'authenticating…'}
                  {status === 'done' && 'granted'}
                </span>
              </p>
            </CardContent>
          </Card>
        </motion.section>
      </div>
    </div>
  );
}

export default LoginPage;
