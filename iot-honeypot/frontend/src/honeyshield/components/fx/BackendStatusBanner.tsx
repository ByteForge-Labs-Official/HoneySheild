/**
 * Inline status banner shown above the SOC hero.
 * Shows live backend connection state + login/logout actions.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Loader2, LogIn, LogOut, RefreshCcw, Wifi, WifiOff } from 'lucide-react';
import { useState } from 'react';
import { useBackend } from '../../lib/backend-context';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

export function BackendStatusBanner() {
  const { status, version, usingMock, lastError, refresh, login, logout } = useBackend();
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  const isOnline = status === 'online';
  const isOffline = status === 'offline';
  const isChecking = status === 'checking';

  const tone = isOnline
    ? 'border-[#00FF88]/40 bg-[#00FF88]/5 text-[#00FF88]'
    : isOffline
      ? 'border-[#FF3D6E]/40 bg-[#FF3D6E]/5 text-[#FF3D6E]'
      : 'border-[#FFD600]/40 bg-[#FFD600]/5 text-[#FFD600]';

  const Icon = isOnline ? Wifi : isOffline ? WifiOff : isChecking ? Loader2 : Activity;

  const handleLogin = async () => {
    if (!username || !password) return;
    setBusy(true);
    await login(username, password);
    setBusy(false);
    setOpen(false);
    setPassword('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="container relative z-30 mt-4 md:mt-6"
    >
      <div
        className={`flex flex-col gap-3 rounded-xl border px-4 py-3 backdrop-blur md:flex-row md:items-center md:justify-between ${tone}`}
      >
        <div className="flex items-center gap-3">
          <Icon
            className={`h-4 w-4 ${isChecking ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          <div className="flex flex-wrap items-center gap-2 text-xs md:text-sm">
            <span className="font-semibold uppercase tracking-wider">
              {isChecking ? 'Probing backend' : isOnline ? 'Backend online' : 'Backend offline'}
            </span>
            {version && (
              <span className="font-mono text-[10px] opacity-70">v{version}</span>
            )}
            {isOnline && usingMock && (
              <span className="text-[#FFD600]">
                • Authenticate to load live honeypot data
              </span>
            )}
            {isOffline && (
              <span className="text-[#FF3D6E]">
                • Demo mode (mock data) — start the FastAPI service to connect
              </span>
            )}
            {lastError && <span className="text-[#FF3D6E]">{lastError}</span>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => void refresh()}
            aria-label="Refresh backend status"
          >
            <RefreshCcw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
          {isOnline ? (
            <Button size="sm" variant="outline" onClick={() => void logout()}>
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setOpen((v) => !v)}
              disabled={isOffline}
            >
              <LogIn className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{open ? 'Cancel' : 'Sign in'}</span>
            </Button>
          )}
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="mt-3 grid grid-cols-1 gap-2 rounded-xl border border-[#1F2A44]/80 bg-[#0F1626]/80 p-4 backdrop-blur md:grid-cols-[1fr_1fr_auto]">
              <Input
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void handleLogin();
                }}
              />
              <Button onClick={() => void handleLogin()} disabled={busy}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Connect'}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
