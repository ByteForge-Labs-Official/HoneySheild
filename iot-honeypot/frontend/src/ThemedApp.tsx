import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { SnackbarProvider } from 'notistack';
import App from './App';
import { useAppSelector } from './store/hooks';
import { buildTheme } from './theme/theme';

export const ThemedApp: React.FC = () => {
  const mode = useAppSelector((s) => s.theme.mode);
  const theme = React.useMemo(() => buildTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider
        maxSnack={4}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        autoHideDuration={4500}
      >
        <App />
      </SnackbarProvider>
    </ThemeProvider>
  );
};
