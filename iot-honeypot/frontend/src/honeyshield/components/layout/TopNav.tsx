import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Bell,
  Hexagon,
  LayoutDashboard,
  LogIn,
  LogOut,
  Map,
  PieChart,
  Settings,
  Shield,
} from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'live', label: 'Live Attacks', icon: Activity },
  { id: 'honeypots', label: 'Honeypots', icon: Shield },
  { id: 'intel', label: 'Threat Intel', icon: Bell },
  { id: 'analytics', label: 'Analytics', icon: PieChart },
  { id: 'map', label: 'World Map', icon: Map },
];

export function TopNav({
  active,
  onSelect,
  onOpenNotifications,
  notifications,
}: {
  active: string;
  onSelect: (id: string) => void;
  onOpenNotifications: () => void;
  notifications: number;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [authed, setAuthed] = useState(false);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const sync = () => {
      const token = window.localStorage.getItem('hs_access_token');
      setAuthed(Boolean(token));
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

  const initials = (email ?? 'A').slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-40 border-b border-[#1F2A44]/80 bg-[#0B0F19]/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center gap-6">
        <button
          onClick={() => {
            if (location.pathname !== '/' && location.pathname !== '/honeyshield') {
              navigate('/');
              return;
            }
            onSelect('dashboard');
          }}
          className="group flex items-center gap-2.5 outline-none"
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
              IoT SOC Platform
            </span>
          </span>
        </button>

        <nav className="hidden flex-1 items-center justify-center gap-1 lg:flex">
          {NAV.map((item) => {
            const Icon = item.icon;
            const isActive = active === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (location.pathname !== '/' && location.pathname !== '/honeyshield') {
                    navigate('/');
                  }
                  onSelect(item.id);
                }}
                className={`group relative flex items-center gap-2 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                  isActive ? 'text-[#E6F1FF]' : 'text-[#8A9BB8] hover:text-[#E6F1FF]'
                }`}
              >
                {isActive && (
                  <motion.span
                    layoutId="nav-active-bg"
                    className="absolute inset-0 -z-10 rounded-md border border-[#00BFFF]/40 bg-gradient-to-r from-[#00BFFF]/15 via-[#00E5FF]/10 to-[#00FF88]/15 shadow-[0_0_18px_rgba(0,191,255,0.35)]"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-[#00E5FF]' : ''}`} />
                {item.label}
                {isActive && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-x-2 -bottom-[7px] h-[2px] rounded-full bg-gradient-to-r from-[#00BFFF] via-[#00E5FF] to-[#00FF88] shadow-[0_0_12px_rgba(0,229,255,0.7)]"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}
              </button>
            );
          })}

          <button
            onClick={() => navigate('/settings')}
            className={`group relative flex items-center gap-2 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
              location.pathname === '/settings'
                ? 'text-[#E6F1FF]'
                : 'text-[#8A9BB8] hover:text-[#E6F1FF]'
            }`}
          >
            {location.pathname === '/settings' && (
              <motion.span
                layoutId="nav-active-bg"
                className="absolute inset-0 -z-10 rounded-md border border-[#00BFFF]/40 bg-gradient-to-r from-[#00BFFF]/15 via-[#00E5FF]/10 to-[#00FF88]/15 shadow-[0_0_18px_rgba(0,191,255,0.35)]"
                transition={{ type: 'spring', stiffness: 350, damping: 30 }}
              />
            )}
            <Settings
              className={`h-3.5 w-3.5 ${
                location.pathname === '/settings' ? 'text-[#00E5FF]' : ''
              }`}
            />
            Settings
            {location.pathname === '/settings' && (
              <motion.span
                layoutId="nav-active"
                className="absolute inset-x-2 -bottom-[7px] h-[2px] rounded-full bg-gradient-to-r from-[#00BFFF] via-[#00E5FF] to-[#00FF88] shadow-[0_0_12px_rgba(0,229,255,0.7)]"
                transition={{ type: 'spring', stiffness: 350, damping: 30 }}
              />
            )}
          </button>
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Badge variant="success" className="hidden md:inline-flex">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#00FF88]" />
            SOC Online
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            onClick={onOpenNotifications}
            aria-label="Notifications"
          >
            <div className="relative">
              <Bell className="h-4 w-4 text-[#E6F1FF]" />
              {notifications > 0 && (
                <span className="absolute -right-1.5 -top-1.5 grid h-4 min-w-4 place-items-center rounded-full bg-[#FF3D6E] px-1 text-[9px] font-bold text-white shadow-[0_0_10px_rgba(255,61,110,0.7)]">
                  {notifications}
                </span>
              )}
            </div>
          </Button>

          {authed ? (
            <>
              <button
                onClick={() => navigate('/settings')}
                className="flex items-center gap-2 rounded-full border border-[#1F2A44] bg-[#0F1626]/80 py-1 pl-1 pr-3 transition hover:border-[#00BFFF]/50"
                title="Open settings"
              >
                <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-[#00BFFF] to-[#00FF88] text-[10px] font-bold text-[#001018]">
                  {initials}
                </span>
                <span className="hidden text-xs font-medium text-[#E6F1FF] md:inline">
                  {email ?? 'analyst'}
                </span>
              </button>
              <Button variant="ghost" size="icon" onClick={signOut} aria-label="Sign out">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              onClick={() => navigate('/login')}
              className="ml-1"
              aria-label="Sign in"
            >
              <LogIn className="mr-1.5 h-3.5 w-3.5" /> Sign in
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}