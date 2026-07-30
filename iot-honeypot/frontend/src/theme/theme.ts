import { createTheme, type Theme } from '@mui/material/styles';

export type ThemeMode = 'light' | 'dark';

const sharedComponents = {
  MuiButton: {
    styleOverrides: {
      root: { textTransform: 'none' as const, fontWeight: 600 },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: { backgroundImage: 'none' },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: { backgroundImage: 'none' },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: { backgroundImage: 'none' },
    },
  },
};

export function buildTheme(mode: ThemeMode): Theme {
  return createTheme({
    palette: {
      mode,
      primary: { main: mode === 'dark' ? '#60a5fa' : '#1976d2' },
      secondary: { main: '#f97316' },
      success: { main: '#22c55e' },
      error: { main: '#ef4444' },
      warning: { main: '#f59e0b' },
      info: { main: '#06b6d4' },
      background: {
        default: mode === 'dark' ? '#0b1220' : '#f4f6fb',
        paper: mode === 'dark' ? '#111a2e' : '#ffffff',
      },
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily:
        "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      h4: { fontWeight: 700 },
      h5: { fontWeight: 700 },
      h6: { fontWeight: 700 },
      button: { textTransform: 'none' as const },
    },
    components: sharedComponents,
  });
}