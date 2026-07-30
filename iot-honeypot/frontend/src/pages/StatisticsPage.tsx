import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Box,
} from '@mui/material';
import dayjs from 'dayjs';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { PageHeader } from '@/components/common/PageHeader';
import { usePageTitle } from '@/hooks/usePageTitle';
import { AttackTimelineChart } from '@/components/charts/AttackTimelineChart';
import { ProtocolPieChart } from '@/components/charts/ProtocolPieChart';
import { SeverityBarChart } from '@/components/charts/SeverityBarChart';
import { TopIpsChart } from '@/components/charts/TopIpsChart';
import { useAppSelector } from '@/store/hooks';

type Range = '1h' | '24h' | '7d' | '30d';

export const StatisticsPage: React.FC = () => {
  usePageTitle('Statistics');
  const [range, setRange] = useState<Range>('24h');
  const stats = useAppSelector((s) => s.attacks.stats);

  // Build a per-protocol timeline by replaying rough distribution
  const stacked = (stats?.timeline ?? []).map((b, idx) => {
    const protoKeys = Object.keys(stats?.by_protocol ?? {});
    const ratio = 1 / Math.max(1, protoKeys.length);
    const out: Record<string, number | string> = { bucket: b.bucket };
    protoKeys.forEach((p) => {
      out[p] = Math.round(b.count * ratio * (0.7 + Math.sin(idx + p.length) * 0.2));
    });
    return out;
  });

  const protocols = Object.keys(stats?.by_protocol ?? {});

  return (
    <Box>
      <PageHeader
        title="Statistics"
        subtitle="Historical attack trends and breakdowns"
        actions={
          <ToggleButtonGroup
            value={range}
            exclusive
            size="small"
            onChange={(_, v: Range | null) => v && setRange(v)}
          >
            <ToggleButton value="1h">1h</ToggleButton>
            <ToggleButton value="24h">24h</ToggleButton>
            <ToggleButton value="7d">7d</ToggleButton>
            <ToggleButton value="30d">30d</ToggleButton>
          </ToggleButtonGroup>
        }
      />

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                Stacked timeline ({range})
              </Typography>
              <Box sx={{ height: 340 }}>
                <ResponsiveContainer>
                  <LineChart data={stacked}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="bucket"
                      tickFormatter={(v) => dayjs(v).format('HH:mm')}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      labelFormatter={(v) => dayjs(v as string).format('YYYY-MM-DD HH:mm')}
                    />
                    <Legend />
                    {protocols.map((p, i) => (
                      <Line
                        key={p}
                        type="monotone"
                        dataKey={p}
                        stroke={
                          ['#1976d2', '#06b6d4', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#64748b'][
                            i % 7
                          ]
                        }
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <ProtocolPieChart />
        </Grid>
        <Grid item xs={12} md={6}>
          <SeverityBarChart />
        </Grid>

        <Grid item xs={12} md={8}>
          <AttackTimelineChart />
        </Grid>
        <Grid item xs={12} md={4}>
          <TopIpsChart />
        </Grid>
      </Grid>
    </Box>
  );
};