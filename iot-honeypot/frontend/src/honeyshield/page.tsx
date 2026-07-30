import { AnimatePresence, motion } from 'framer-motion';
import { useState } from 'react';
import { BackgroundFX } from './components/fx/BackgroundFX';
import { BackendStatusBanner } from './components/fx/BackendStatusBanner';
import { Footer } from './components/layout/Footer';
import { NotificationCenter } from './components/layout/NotificationCenter';
import { TopNav } from './components/layout/TopNav';
import { BackendProvider } from './lib/backend-context';
import { AIPanel } from './section/AIPanel';
import { Analytics } from './section/Analytics';
import { AttackTimeline } from './section/AttackTimeline';
import { Hero } from './section/Hero';
import { HoneypotManagement } from './section/HoneypotManagement';
import { LiveAttackFeed } from './section/LiveAttackFeed';
import { SettingsPanel } from './section/SettingsPanel';
import { StatsGrid } from './section/StatsGrid';
import { ThreatIntel } from './section/ThreatIntel';
import { WorldMap } from './section/WorldMap';

export function HoneyShieldPage() {
  const [active, setActive] = useState('dashboard');
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  function scrollTo(id: string) {
    setActive(id);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <BackendProvider>
      <div className="relative min-h-screen overflow-hidden text-[#E6F1FF]">
        <BackgroundFX />
        <TopNav
          active={active}
          onSelect={scrollTo}
          onOpenNotifications={() => setNotificationsOpen(true)}
          notifications={5}
        />
        <BackendStatusBanner />
        <NotificationCenter open={notificationsOpen} onClose={() => setNotificationsOpen(false)} />

        <main className="relative">
          <AnimatePresence mode="wait">
            <motion.div
              key="page"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.4 }}
            >
              <Hero
                onStartMonitoring={() => scrollTo('dashboard')}
                onLiveAttacks={() => scrollTo('live')}
              />
              <StatsGrid />
              <LiveAttackFeed />
              <WorldMap />
              <Analytics />
              <ThreatIntel />
              <AIPanel />
              <HoneypotManagement />
              <AttackTimeline />
              <SettingsPanel />
            </motion.div>
          </AnimatePresence>
        </main>
        <Footer />
      </div>
    </BackendProvider>
  );
}