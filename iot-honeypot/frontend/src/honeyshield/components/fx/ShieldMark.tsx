import { motion } from 'framer-motion';

/** Glowing animated shield for hero/logo. */
export function ShieldMark({ size = 220 }: { size?: number }) {
  return (
    <motion.svg
      viewBox="0 0 200 220"
      width={size}
      height={size}
      initial={{ rotate: -2, opacity: 0 }}
      animate={{ rotate: 0, opacity: 1 }}
      transition={{ duration: 1.2, ease: 'easeOut' }}
      className="drop-shadow-[0_0_24px_rgba(0,191,255,0.6)]"
    >
      <defs>
        <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00BFFF" />
          <stop offset="55%" stopColor="#00E5FF" />
          <stop offset="100%" stopColor="#00FF88" />
        </linearGradient>
        <radialGradient id="halo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(0,229,255,0.55)" />
          <stop offset="100%" stopColor="rgba(0,229,255,0)" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="110" r="98" fill="url(#halo)">
        <animate attributeName="r" values="92;108;92" dur="4s" repeatCount="indefinite" />
      </circle>
      <polygon
        points="100,12 178,52 178,138 100,206 22,138 22,52"
        fill="rgba(11,15,25,0.9)"
        stroke="url(#sg)"
        strokeWidth="3"
      />
      <polygon
        points="100,40 156,68 156,128 100,176 44,128 44,68"
        fill="rgba(0,191,255,0.05)"
        stroke="#00E5FF"
        strokeOpacity="0.4"
        strokeWidth="1.5"
      />
      <path
        d="M70 110 L92 132 L138 86"
        fill="none"
        stroke="url(#sg)"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <motion.circle
        cx="100"
        cy="110"
        r="86"
        fill="none"
        stroke="#00BFFF"
        strokeOpacity="0.6"
        strokeWidth="1"
        strokeDasharray="4 8"
        animate={{ rotate: 360 }}
        transition={{ duration: 22, repeat: Infinity, ease: 'linear' }}
        style={{ transformOrigin: '100px 110px' }}
      />
    </motion.svg>
  );
}