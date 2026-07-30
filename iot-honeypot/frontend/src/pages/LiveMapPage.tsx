import React from 'react';
import { Grid, Card, CardContent, Stack, Typography, Box } from '@mui/material';
import { AttackMap } from '@/components/map/AttackMap';
import { PageHeader } from '@/components/common/PageHeader';
import { usePageTitle } from '@/hooks/usePageTitle';
import { useAppSelector } from '@/store/hooks';
import { compactNumber, fromNow } from '@/utils/format';

export const LiveMapPage: React.FC = () => {
  usePageTitle('Live attack map');
  const attacks = useAppSelector((s) => s.attacks.recent);
  const stats = useAppSelector((s) => s.attacks.stats);
  const geo = stats?.by_country ?? [];

  return (
    <Box>
      <PageHeader
        title="Live attack map"
        subtitle="Geolocation of incoming attack sources — updates in real-time via WebSocket"
      />

      <Grid container spacing={3}>
        <Grid item xs={12} md={9}>
          <AttackMap attacks={attacks} geo={geo} live />
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                Top countries
              </Typography>
              <Stack divider={<Box sx={{ borderTop: 1, borderColor: 'divider' }} />}>
                {geo.slice(0, 10).map((g) => (
                  <Stack
                    key={g.country}
                    direction="row"
                    justifyContent="space-between"
                    sx={{ py: 1.5 }}
                  >
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {g.country}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {fromNow(new Date().toISOString())}
                      </Typography>
                    </Box>
                    <Typography variant="body2" fontWeight={700}>
                      {compactNumber(g.count)}
                    </Typography>
                  </Stack>
                ))}
                {geo.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    Awaiting first attack…
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