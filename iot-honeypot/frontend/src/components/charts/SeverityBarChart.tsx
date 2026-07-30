import React from 'react';
import { Card, CardContent, CardHeader, Skeleton } from '@mui/material';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { useAppSelector } from '@/store/hooks';

const COLOR_MAP: Record<string, string> = {
  low: '#06b6d4',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#7f1d1d',
};

export const SeverityBarChart: React.FC = () => {
  const stats = useAppSelector((s) => s.attacks.stats);
  const data = stats
    ? Object.entries(stats.by_severity).map(([k, v]) => ({
        name: k.toUpperCase(),
        value: v,
      }))
    : [];

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Severity distribution"
        titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
      />
      <CardContent sx={{ height: 280 }}>
        {data.length === 0 ? (
          <Skeleton variant="rectangular" height="100%" />
        ) : (
          <ResponsiveContainer>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {data.map((d, idx) => (
                  <Cell key={idx} fill={COLOR_MAP[d.name.toLowerCase()] ?? '#64748b'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};