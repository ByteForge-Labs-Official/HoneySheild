import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, Bell, Bug, Check, CheckCheck, Radar, Skull, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
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
  const [list, setList] = useState(initial);
  const [acked, setAcked] = useState<Set<string>>(new Set());

  const asId = (n: { id: number | string }): string => String(n.id);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  function acknowledgeAll() {
    setAcked(new Set(list.map((n) => asId(n))));
  }

  function clearAll() {
    setList([]);
    setAcked(new Set());
  }

  function acknowledge(id: string) {
    setAcked((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }

  function dismiss(id: string) {
    setList((prev) => prev.filter((n) => asId(n) !== id));
  }

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
                <Badge variant="danger">{list.length}</Badge>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={acknowledgeAll}
                  disabled={list.length === 0 || acked.size === list.length}
                  className="text-[10px] uppercase tracking-wider text-[#00FF88] hover:text-[#00FF88]/80"
                  aria-label="Acknowledge all"
                >
                  <CheckCheck className="mr-1 h-3.5 w-3.5" />
                  Ack all
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAll}
                  disabled={list.length === 0}
                  className="text-[10px] uppercase tracking-wider text-[#FF3D6E] hover:text-[#FF3D6E]/80"
                  aria-label="Clear all"
                >
                  <Trash2 className="mr-1 h-3.5 w-3.5" />
                  Clear
                </Button>
                <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </header>
            <ScrollArea className="h-[calc(100%-72px)]">
              <ul className="flex flex-col gap-2 p-4">
                {list.map((n, i) => {
                  const Icon = ICONS[n.icon];
                  const isAcked = acked.has(asId(n));
                  return (
                    <motion.li
                      key={n.id}
                      initial={{ opacity: 0, x: 30 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.05 * i }}
                      className={
                        'group relative overflow-hidden rounded-lg border p-4 transition ' +
                        (isAcked
                          ? 'border-[#00FF88]/30 bg-[#0B0F19]/40 opacity-60'
                          : 'border-[#1F2A44] bg-[#0F1626]/70 hover:border-[#00BFFF]/50')
                      }
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
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-semibold text-[#E6F1FF]">{n.title}</p>
                            {isAcked && (
                              <Badge variant="success" className="shrink-0 text-[9px]">
                                Acked
                              </Badge>
                            )}
                          </div>
                          <p className="mt-0.5 text-xs text-[#8A9BB8]">{n.body}</p>
                          <div className="mt-2 flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                            <button
                              type="button"
                              onClick={() => acknowledge(asId(n))}
                              disabled={isAcked}
                              className="inline-flex items-center gap-1 rounded-md border border-[#00FF88]/40 bg-[#00FF88]/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-[#00FF88] hover:bg-[#00FF88]/20 disabled:opacity-40"
                            >
                              <Check className="h-3 w-3" /> Acknowledge
                            </button>
                            <button
                              type="button"
                              onClick={() => dismiss(asId(n))}
                              className="inline-flex items-center gap-1 rounded-md border border-[#FF3D6E]/40 bg-[#FF3D6E]/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-[#FF3D6E] hover:bg-[#FF3D6E]/20"
                              aria-label={`Dismiss ${n.title}`}
                            >
                              <Trash2 className="h-3 w-3" /> Dismiss
                            </button>
                          </div>
                        </div>
                      </div>
                    </motion.li>
                  );
                })}
                {list.length === 0 && (
                  <li className="grid place-items-center rounded-lg border border-dashed border-[#1F2A44] bg-[#0B0F19]/40 px-4 py-12 text-center text-xs text-[#8A9BB8]">
                    <Check className="mb-2 h-6 w-6 text-[#00FF88]" />
                    Inbox zero. All notifications cleared.
                  </li>
                )}
              </ul>
            </ScrollArea>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}