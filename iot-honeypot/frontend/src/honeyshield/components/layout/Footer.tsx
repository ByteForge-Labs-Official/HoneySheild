import { Github, Heart, Linkedin, Twitter } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="relative mt-16 border-t border-[#1F2A44]/80 bg-[#0B0F19]/70 backdrop-blur-xl">
      <div className="pointer-events-none absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-[#00BFFF]/60 to-transparent" />
      <div className="container py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <span className="relative grid h-9 w-9 place-items-center rounded-lg border border-[#00BFFF]/40 bg-gradient-to-br from-[#00BFFF]/20 to-[#00FF88]/10 shadow-[0_0_18px_rgba(0,191,255,0.35)]">
              <Heart className="h-4 w-4 text-[#FF3D6E]" />
              <span className="absolute -bottom-1 -right-1 grid h-3.5 w-3.5 place-items-center rounded-full border border-[#0B0F19] bg-[#00FF88]/90">
                <span className="h-1 w-1 rounded-full bg-[#0B0F19]" />
              </span>
            </span>
            <div>
              <p className="font-display text-sm font-semibold text-[#E6F1FF]">HoneyShield AI</p>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8A9BB8]">
                Hackathon Project · IoT SOC
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs">
            <Link to="/login" className="group relative text-[#8A9BB8] transition hover:text-[#E6F1FF]">
              Sign in
              <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-[#00BFFF] to-[#00E5FF] transition-all duration-300 group-hover:w-full" />
            </Link>
            <Link to="/settings" className="group relative text-[#8A9BB8] transition hover:text-[#E6F1FF]">
              Settings
              <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-[#00BFFF] to-[#00E5FF] transition-all duration-300 group-hover:w-full" />
            </Link>
            <a href="#honeypots" className="group relative text-[#8A9BB8] transition hover:text-[#E6F1FF]">
              Honeypots
              <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-[#00BFFF] to-[#00E5FF] transition-all duration-300 group-hover:w-full" />
            </a>
            <a href="#intel" className="group relative text-[#8A9BB8] transition hover:text-[#E6F1FF]">
              Threat intel
              <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-[#00BFFF] to-[#00E5FF] transition-all duration-300 group-hover:w-full" />
            </a>
          </div>
          <p className="text-xs text-[#8A9BB8]">
            Built with{' '}
            <span className="text-[#00E5FF]">React</span>,{' '}
            <span className="text-[#00E5FF]">Tailwind CSS</span>,{' '}
            <span className="text-[#00E5FF]">Framer Motion</span> &{' '}
            <span className="text-[#00E5FF]">Recharts</span>.
          </p>
          <div className="flex items-center gap-2">
            {[Github, Twitter, Linkedin].map((Icon, i) => (
              <a
                key={i}
                href="#"
                className="grid h-9 w-9 place-items-center rounded-md border border-[#1F2A44] bg-[#0F1626]/70 text-[#8A9BB8] transition hover:border-[#00BFFF]/50 hover:text-[#E6F1FF] hover:shadow-[0_0_18px_rgba(0,191,255,0.35)]"
              >
                <Icon className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}