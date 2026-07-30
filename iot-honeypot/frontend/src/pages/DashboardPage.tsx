import React, { useEffect } from 'react';
import { Grid, Stack, Card, CardContent, Typography, Box, Chip } from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import PublicIcon from '@mui/icons-material/Public';
import BugReportIcon from '@mui/icons-material/BugReport';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';

import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAttacks, fetchStats, attacksActions } from '@/store/slices/attacksSlice';
import { fetchAlerts } from '@/store/slices/alertsSlice';
import { generateDemoStats } from '@/utils/demoData';
import { StatCard } from '@/components/common/StatCard';
import { PageHeader } from '@/components/common/PageHeader';
import { AttackTimelineChart } from '@/components/charts/AttackTimelineChart';
import { ProtocolPieChart } from '@/components/charts/ProtocolPieChart';
import { SeverityBarChart } from '@/components/charts/SeverityBarChart';
import { compactNumber, fromNow } from '@/utils/format';
import { usePageTitle } from '@/hooks/usePageTitle';
import { AlertsList } from '@/components/tables/AlertsList';

const DEMO_MODE = import.meta.env.VITE_ENABLE_DEMO_MODE === 'true';

export const DashboardPage: React.FC = () => {
  usePageTitle('Dashboard');
  const dispatch = useAppDispatch();
  const stats = useAppSelector((s) => s.attacks.stats);
  const recent = useAppSelector((s) => s.attacks.recent);
  const alerts = useAppSelector((s) => s.alerts.items).slice(0, 5);

  useEffect(() => {
    const loadData = () => {
      dispatch(fetchStats()).catch(() => {
        if (DEMO_MODE) {
          dispatch(attacksActions.setStats(generateDemoStats()));
        }
      });
      dispatch(fetchAttacks()).catch(() => {});
      dispatch(fetchAlerts()).catch(() => {});
    };

    loadData();
    const timer = setInterval(loadData, 3000);
    return () => clearInterval(timer);
  }, [dispatch]);

  // Demo fallback: seed stats from local generator when no real data
  const effective = stats ?? (DEMO_MODE ? generateDemoStats() : null);

  return (
    <Box>
      <PageHeader
        title="Security overview"
        subtitle="Real-time IoT honeypot activity and attack intelligence"
        actions={
          <Chip
            label="LIVE"
            color="success"
            variant="outlined"
            sx={{ fontWeight: 700 }}
          />
        }
      />

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total attacks"
            value={compactNumber(effective?.total ?? 0)}
            icon={<SecurityIcon />}
            color="primary"
            delta={12}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unique countries"
            value={effective?.by_country.length ?? 0}
            icon={<PublicIcon />}
            color="info"
            delta={3}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active honeypots"
            value={Object.keys(effective?.by_protocol ?? {}).length}
            icon={<BugReportIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Unread alerts"
            value={alerts.filter((a) => !a.acknowledged).length}
            icon={<NotificationsActiveIcon />}
            color="error"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <AttackTimelineChart />
        </Grid>
        <Grid item xs={12} md={4}>
          <ProtocolPieChart />
        </Grid>
        <Grid item xs={12} md={6}>
          <SeverityBarChart />
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                Recent alerts
              </Typography>
              <AlertsList items={alerts} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                Latest attacks
              </Typography>
              <Stack divider={<Box sx={{ borderTop: 1, borderColor: 'divider' }} />}>
                {recent.slice(0, 8).map((a) => (
                  <Stack
                    key={a.id}
                    direction={{ xs: 'column', sm: 'row' }}
                    justifyContent="space-between"
                    spacing={1}
                    sx={{ py: 1.5 }}
                  >
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {a.source_ip} → {a.honeypot_name ?? a.protocol}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {a.country ?? '—'} · {a.payload_summary ?? 'no payload'}
                      </Typography>
                    </Box>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Chip
                        size="small"
                        label={a.severity.toUpperCase()}
                        color={
                          a.severity === 'critical' || a.severity === 'high'
                            ? 'error'
                            : 'warning'
                        }
                        variant="outlined"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {fromNow(a.timestamp)}
                      </Typography>
                    </Stack>
                  </Stack>
                ))}
                {recent.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No live attacks yet — waiting for traffic…
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};