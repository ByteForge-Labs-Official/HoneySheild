import { motion } from 'framer-motion';
import { ArrowRight, Play, ShieldCheck, Sparkles } from 'lucide-react';
import { Button } from '../components/ui/button';
import { ShieldMark } from '../components/fx/ShieldMark';

export function Hero({
  onStartMonitoring,
  onLiveAttacks,
}: {
  onStartMonitoring: () => void;
  onLiveAttacks: () => void;
}) {
  return (
    <section className="relative overflow-hidden">
      <div className="container relative grid items-center gap-10 py-20 md:grid-cols-[1.1fr_0.9fr] md:py-28">
        <div>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#00BFFF]/40 bg-[#00BFFF]/10 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-[#00BFFF]"
          >
            <Sparkles className="h-3 w-3" />
            AI-Powered Deception Platform
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="font-display text-4xl font-semibold leading-tight tracking-tight text-[#E6F1FF] md:text-5xl lg:text-6xl"
          >
            Protecting{' '}
            <span className="neon-text bg-gradient-to-br from-[#00BFFF] via-[#00E5FF] to-[#00FF88] bg-clip-text text-transparent">
              IoT Networks
            </span>{' '}
            Through{' '}
            <span className="relative inline-block">
              Intelligent
              <motion.span
                className="absolute -bottom-1 left-0 h-1 rounded-full bg-gradient-to-r from-[#00BFFF] to-[#00FF88]"
                initial={{ width: 0 }}
                animate={{ width: '100%' }}
                transition={{ delay: 0.8, duration: 1.1 }}
              />
            </span>{' '}
            Deception
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mt-5 max-w-2xl text-base text-[#8A9BB8] md:text-lg"
          >
            Monitor attackers in real time, analyze malicious behavior, visualize attack trends,
            and improve IoT security using AI-powered honeypots.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Button size="lg" onClick={onStartMonitoring}>
              Start Monitoring
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" onClick={onLiveAttacks}>
              <Play className="h-4 w-4" />
              View Live Attacks
            </Button>
            <div className="ml-2 flex items-center gap-2 text-xs text-[#8A9BB8]">
              <ShieldCheck className="h-4 w-4 text-[#00FF88]" /> Trusted by SOC teams worldwide
            </div>
          </motion.div>
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="relative grid place-items-center"
        >
          <div className="absolute inset-0 -z-10 rounded-full bg-[radial-gradient(circle,rgba(0,229,255,0.35),transparent_60%)] blur-3xl" />
          <div className="circuit-bg absolute inset-0 -z-10 rounded-2xl opacity-50" />
          <motion.div
            className="absolute h-[320px] w-[320px] rounded-full border border-[#00BFFF]/30"
            animate={{ rotate: 360 }}
            transition={{ duration: 22, repeat: Infinity, ease: 'linear' }}
            style={{ borderTopColor: '#00E5FF', borderRightColor: 'transparent', borderBottomColor: 'transparent', borderLeftColor: 'transparent' }}
          />
          <motion.div
            className="absolute h-[360px] w-[360px] rounded-full border border-[#00FF88]/15"
            animate={{ rotate: -360 }}
            transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
            style={{ borderTopColor: 'transparent', borderRightColor: '#00FF88', borderBottomColor: 'transparent', borderLeftColor: 'transparent' }}
          />
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 3.4, repeat: Infinity, ease: 'easeInOut' }}
          >
            <ShieldMark size={280} />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}