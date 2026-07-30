import React from 'react';
import { Card, CardContent, CardHeader, Skeleton } from '@mui/material';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import dayjs from 'dayjs';
import { useAppSelector } from '@/store/hooks';

export const AttackTimelineChart: React.FC = () => {
  const stats = useAppSelector((s) => s.attacks.stats);
  const data = stats?.timeline ?? [];

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Attack timeline (last 24h)"
        titleTypographyProps={{ variant: 'subtitle1', fontWeight: 700 }}
      />
      <CardContent sx={{ height: 280 }}>
        {data.length === 0 ? (
          <Skeleton variant="rectangular" height="100%" />
        ) : (
          <ResponsiveContainer>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="atkGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis
                dataKey="bucket"
                tickFormatter={(v) => dayjs(v).format('HH:mm')}
                tick={{ fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                labelFormatter={(v) => dayjs(v as string).format('YYYY-MM-DD HH:mm')}
                contentStyle={{
                  borderRadius: 8,
                  border: 'none',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#ef4444"
                fill="url(#atkGrad)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};