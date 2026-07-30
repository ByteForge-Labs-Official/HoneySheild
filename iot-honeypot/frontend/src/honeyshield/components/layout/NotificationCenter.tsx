import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, Bell, Bug, Check, Radar, Skull, X } from 'lucide-react';
import { useEffect } from 'react';
import { notifications as initial } from '../../lib/mock-data';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';

const ICONS = {
  skull: Skull,
  bug: Bug,
  radar: Radar,
  alert: AlertTriangle,
  check: Check,
} as const;

export function NotificationCenter({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.aside
            initial={{ x: 480, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 480, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 26 }}
            className="fixed right-0 top-0 z-50 h-full w-full max-w-md border-l border-[#1F2A44] bg-gradient-to-br from-[#0F1626] to-[#0B0F19] shadow-[-20px_0_60px_rgba(0,191,255,0.18)]"
          >
            <header className="flex items-center justify-between border-b border-[#1F2A44] p-5">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-[#00BFFF]" />
                <h2 className="font-display text-sm font-semibold tracking-wide text-[#E6F1FF]">
                  Notification Center
                </h2>
                <Badge variant="danger">{initial.length}</Badge>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </header>
            <ScrollArea className="h-[calc(100%-72px)]">
              <ul className="flex flex-col gap-2 p-4">
                {initial.map((n, i) => {
                  const Icon = ICONS[n.icon];
                  return (
                    <motion.li
                      key={n.id}
                      initial={{ opacity: 0, x: 30 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.05 * i }}
                      className="group relative overflow-hidden rounded-lg border border-[#1F2A44] bg-[#0F1626]/70 p-4 hover:border-[#00BFFF]/50"
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className={`grid h-8 w-8 shrink-0 place-items-center rounded-md border ${
                            n.tone === 'critical'
                              ? 'border-[#FF3D6E]/50 bg-[#FF3D6E]/10 text-[#FF3D6E]'
                              : n.tone === 'high'
                                ? 'border-[#FF8A1F]/50 bg-[#FF8A1F]/10 text-[#FF8A1F]'
                                : 'border-[#00FF88]/40 bg-[#00FF88]/10 text-[#00FF88]'
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold text-[#E6F1FF]">{n.title}</p>
                          <p className="mt-0.5 text-xs text-[#8A9BB8]">{n.body}</p>
                        </div>
                      </div>
                    </motion.li>
                  );
                })}
              </ul>
            </ScrollArea>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}