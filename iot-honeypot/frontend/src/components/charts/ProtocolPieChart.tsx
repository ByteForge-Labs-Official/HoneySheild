import React from 'react';
import { Card, CardContent, CardHeader, Skeleton } from '@mui/material';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { useAppSelector } from '@/store/hooks';

const COLORS = ['#1976d2', '#06b6d4', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#64748b'];

export const ProtocolPieChart: React.FC = () => {
  const stats = useAppSelector((s) => s.attacks.stats);
  const entries = stats
    ? Object.entries(stats.by_protocol).map(([k, v]) => ({ name: k.toUpperCase(), value: v }))
    : [];

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Attacks by protocol"
        titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
      />
      <CardContent sx={{ height: 280 }}>
        {entries.length === 0 ? (
          <Skeleton variant="rectangular" height="100%" />
        ) : (
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={entries}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
              >
                {entries.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};