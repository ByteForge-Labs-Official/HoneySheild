import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Stack,
  FormControlLabel,
  Switch,
  Divider,
  Typography,
  Button,
  Box,
} from '@mui/material';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import { PageHeader } from '@/components/common/PageHeader';
import { usePageTitle } from '@/hooks/usePageTitle';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { themeActions } from '@/store/slices/themeSlice';
import { logoutThunk } from '@/store/slices/authSlice';
import { useNavigate } from 'react-router-dom';

export const SettingsPage: React.FC = () => {
  usePageTitle('Settings');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const mode = useAppSelector((s) => s.theme.mode);
  const user = useAppSelector((s) => s.auth.user);

  return (
    <Box>
      <PageHeader title="Settings" subtitle="Application preferences and account" />

      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="Appearance"
          titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
        />
        <Divider />
        <CardContent>
          <Stack spacing={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={mode === 'dark'}
                  onChange={() => dispatch(themeActions.toggle())}
                  icon={<DarkModeIcon />}
                />
              }
              label={`Dark mode (${mode === 'dark' ? 'on' : 'off'})`}
            />
            <Typography variant="body2" color="text.secondary">
              Theme preference is persisted in <code>localStorage</code> and follows your
              OS preference on first visit.
            </Typography>
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="Account"
          titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
        />
        <Divider />
        <CardContent>
          <Stack spacing={1}>
            <Typography variant="body2">
              <b>Username:</b> {user?.username ?? '—'}
            </Typography>
            <Typography variant="body2">
              <b>Role:</b> {user?.role ?? '—'}
            </Typography>
            <Typography variant="body2">
              <b>Email:</b> {user?.email ?? '—'}
            </Typography>
            <Button
              color="error"
              variant="outlined"
              sx={{ mt: 2, alignSelf: 'flex-start' }}
              onClick={() => dispatch(logoutThunk()).then(() => navigate('/login'))}
            >
              Log out
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title="About"
          titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
        />
        <Divider />
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Honeynet Dashboard v1.0.0 — IoT Honeynet Research Platform
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};