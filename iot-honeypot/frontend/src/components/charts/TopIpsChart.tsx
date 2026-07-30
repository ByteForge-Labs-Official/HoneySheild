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
} from 'recharts';
import { useAppSelector } from '@/store/hooks';

export const TopIpsChart: React.FC = () => {
  const stats = useAppSelector((s) => s.attacks.stats);
  const data = (stats?.top_ips ?? []).slice(0, 10);

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Top attacker IPs"
        titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
      />
      <CardContent sx={{ height: 320 }}>
        {data.length === 0 ? (
          <Skeleton variant="rectangular" height="100%" />
        ) : (
          <ResponsiveContainer>
            <BarChart data={data} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="ip" type="category" tick={{ fontSize: 12 }} width={120} />
              <Tooltip />
              <Bar dataKey="count" fill="#1976d2" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};