import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

export function SectionHeader({
  eyebrow,
  title,
  subtitle,
  right,
}: {
  eyebrow?: string;
  title: ReactNode;
  subtitle?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        {eyebrow && (
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-[#00BFFF]/40 bg-[#00BFFF]/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-[#00BFFF]">
            <span className="h-1.5 w-1.5 animate-pulse-glow rounded-full bg-[#00FF88]" />
            {eyebrow}
          </div>
        )}
        <motion.h2
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5 }}
          className="font-display text-2xl font-semibold tracking-tight text-[#E6F1FF] md:text-3xl"
        >
          {title}
        </motion.h2>
        {subtitle && (
          <p className="mt-2 max-w-2xl text-sm text-[#8A9BB8]">{subtitle}</p>
        )}
      </div>
      {right && <div className="flex items-center gap-2">{right}</div>}
    </div>
  );
}