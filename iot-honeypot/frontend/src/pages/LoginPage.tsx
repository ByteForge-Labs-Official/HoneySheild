import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Stack,
  Alert,
  IconButton,
  Tooltip,
  InputAdornment,
  Divider,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import ShieldIcon from '@mui/icons-material/Shield';

import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { loginThunk, clearError } from '@/store/slices/authSlice';
import { themeActions } from '@/store/slices/themeSlice';

export const LoginPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { status, error } = useAppSelector((s) => s.auth);
  const mode = useAppSelector((s) => s.theme.mode);

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [showPwd, setShowPwd] = useState(false);

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await dispatch(loginThunk({ username, password }));
    if (loginThunk.fulfilled.match(result)) navigate(from, { replace: true });
  };

  const fillDemo = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        backgroundImage: (t) =>
          t.palette.mode === 'dark'
            ? 'radial-gradient(1200px 600px at 80% -10%, rgba(96,165,250,0.15), transparent), radial-gradient(800px 600px at -10% 110%, rgba(249,115,22,0.12), transparent)'
            : 'radial-gradient(1200px 600px at 80% -10%, rgba(25,118,210,0.18), transparent), radial-gradient(800px 600px at -10% 110%, rgba(249,115,22,0.12), transparent)',
        p: 2,
      }}
    >
      <Tooltip title={mode === 'dark' ? 'Light mode' : 'Dark mode'}>
        <IconButton
          sx={{ position: 'absolute', top: 16, right: 16 }}
          onClick={() => dispatch(themeActions.toggle())}
        >
          {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
        </IconButton>
      </Tooltip>

      <Card
        sx={{
          width: '100%',
          maxWidth: 420,
          boxShadow: (t) => t.shadows[10],
          borderRadius: 3,
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={1.5} sx={{ mb: 3 }}>
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                bgcolor: (t) => t.palette.primary.main + '22',
                color: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldIcon fontSize="large" />
            </Box>
            <Typography variant="h5" fontWeight={800}>
              Honeynet Platform
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sign in to access the operations dashboard
            </Typography>
          </Stack>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => dispatch(clearError())}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <Stack spacing={2}>
              <TextField
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                fullWidth
                required
                autoComplete="username"
              />
              <TextField
                label="Password"
                type={showPwd ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
                required
                autoComplete="current-password"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPwd((v) => !v)} edge="end">
                        {showPwd ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={status === 'loading'}
                sx={{ py: 1.2 }}
              >
                {status === 'loading' ? 'Signing in…' : 'Sign in'}
              </Button>
            </Stack>
          </form>

          <Divider sx={{ my: 3 }}>Demo accounts</Divider>

          <Stack direction="row" spacing={1}>
            <Button
              size="small"
              variant="outlined"
              fullWidth
              onClick={() => fillDemo('admin', 'admin123')}
            >
              Admin
            </Button>
            <Button
              size="small"
              variant="outlined"
              fullWidth
              onClick={() => fillDemo('analyst', 'analyst123')}
            >
              Analyst
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};
