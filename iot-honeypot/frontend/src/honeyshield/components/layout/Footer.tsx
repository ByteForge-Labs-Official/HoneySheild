import { Github, Heart, Linkedin, Twitter } from 'lucide-react';

export function Footer() {
  return (
    <footer className="relative mt-16 border-t border-[#1F2A44]/80 bg-[#0B0F19]/70 backdrop-blur-xl">
      <div className="container py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg border border-[#00BFFF]/40 bg-gradient-to-br from-[#00BFFF]/20 to-[#00FF88]/10">
              <Heart className="h-4 w-4 text-[#FF3D6E]" />
            </span>
            <div>
              <p className="font-display text-sm font-semibold text-[#E6F1FF]">HoneyShield AI</p>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8A9BB8]">
                Hackathon Project · IoT SOC
              </p>
            </div>
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
                className="grid h-9 w-9 place-items-center rounded-md border border-[#1F2A44] bg-[#0F1626]/70 text-[#8A9BB8] transition hover:border-[#00BFFF]/50 hover:text-[#E6F1FF]"
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