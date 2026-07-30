/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '1.5rem',
      screens: { '2xl': '1440px' },
    },
    extend: {
      colors: {
        background: '#0B0F19',
        foreground: '#E6F1FF',
        card: { DEFAULT: '#0F1626', foreground: '#E6F1FF' },
        popover: { DEFAULT: '#0F1626', foreground: '#E6F1FF' },
        primary: { DEFAULT: '#00BFFF', foreground: '#001018' },
        secondary: { DEFAULT: '#0F1626', foreground: '#E6F1FF' },
        muted: { DEFAULT: '#1A2238', foreground: '#8A9BB8' },
        accent: { DEFAULT: '#00E5FF', foreground: '#001018' },
        destructive: { DEFAULT: '#FF3D6E', foreground: '#FFFFFF' },
        border: '#1F2A44',
        input: '#1A2238',
        ring: '#00BFFF',
        success: '#00FF88',
        warning: '#FFB020',
        danger: '#FF3D6E',
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        display: ['"Space Grotesk"', '"Inter"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: '14px',
        md: '10px',
        sm: '6px',
      },
      boxShadow: {
        neon: '0 0 24px rgba(0,191,255,0.35), 0 0 60px rgba(0,229,255,0.15)',
        'neon-green': '0 0 24px rgba(0,255,136,0.4), 0 0 60px rgba(0,255,136,0.18)',
        'neon-red': '0 0 24px rgba(255,61,110,0.4), 0 0 60px rgba(255,61,110,0.15)',
        'inset-glow': 'inset 0 0 30px rgba(0,229,255,0.08)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(rgba(0,191,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(0,191,255,0.06) 1px, transparent 1px)',
        'radial-glow':
          'radial-gradient(ellipse at top, rgba(0,191,255,0.18), transparent 60%)',
        'honey-gradient':
          'linear-gradient(135deg, #00BFFF 0%, #00E5FF 50%, #00FF88 100%)',
      },
      animation: {
        'pulse-glow': 'pulseGlow 2.4s ease-in-out infinite',
        'scan-line': 'scanLine 6s linear infinite',
        'grid-pan': 'gridPan 30s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2.4s linear infinite',
        'fade-up': 'fadeUp 0.6s ease-out both',
      },
      keyframes: {
        pulseGlow: {
          '0%,100%': { boxShadow: '0 0 16px rgba(0,191,255,0.35)' },
          '50%': { boxShadow: '0 0 36px rgba(0,229,255,0.75)' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        gridPan: {
          '0%': { backgroundPosition: '0 0, 0 0' },
          '100%': { backgroundPosition: '60px 60px, 60px 60px' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(14px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
