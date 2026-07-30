import { motion, useReducedMotion } from 'framer-motion';
import { useMemo } from 'react';

/** Layered futuristic backdrop: animated grid + particles + hex glow + scanlines. */
export function BackgroundFX() {
  const reduced = useReducedMotion();
  const particles = useMemo(
    () =>
      Array.from({ length: 28 }).map(() => ({
        x: Math.random() * 100,
        y: Math.random() * 100,
        s: 1 + Math.random() * 2.4,
        d: 8 + Math.random() * 18,
        o: 0.2 + Math.random() * 0.6,
      })),
    []
  );
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 cyber-grid animate-grid-pan opacity-60" />
      <div className="absolute inset-0 hex-pattern opacity-40" />
      <div className="absolute inset-0 bg-radial-glow" />
      {particles.map((p, i) => (
        <motion.span
          key={i}
          className="absolute rounded-full bg-[#00E5FF]"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.s,
            height: p.s,
            boxShadow: `0 0 ${p.s * 6}px rgba(0,229,255,0.7)`,
            opacity: p.o,
          }}
          animate={
            reduced
              ? undefined
              : {
                  y: [0, -20, 0],
                  opacity: [p.o, p.o * 0.3, p.o],
                }
          }
          transition={{ duration: p.d, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
      {/* Conic glow + scan line */}
      <div className="absolute -top-40 left-1/2 h-[600px] w-[1200px] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(0,191,255,0.18),transparent_60%)] blur-3xl" />
      <motion.div
        className="absolute inset-x-0 h-24 bg-gradient-to-b from-transparent via-[#00E5FF]/10 to-transparent"
        animate={reduced ? undefined : { y: ['-100%', '100%'] }}
        transition={{ duration: 9, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  );
}