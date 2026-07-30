import React from 'react';
import { Card, CardContent, Stack, Box, Typography, Skeleton } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  delta?: number;
  deltaLabel?: string;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  loading?: boolean;
  sx?: SxProps<Theme>;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  delta,
  deltaLabel,
  color = 'primary',
  loading,
  sx,
}) => {
  const positive = (delta ?? 0) >= 0;
  return (
    <Card
      sx={{
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        borderTop: 3,
        borderColor: `${color}.main`,
        ...sx,
      }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="overline" color="text.secondary">
              {title}
            </Typography>
            {loading ? (
              <Skeleton variant="text" width={120} height={48} />
            ) : (
              <Typography variant="h4" fontWeight={700} sx={{ mt: 0.5 }}>
                {value}
              </Typography>
            )}
            {delta !== undefined && (
              <Typography
                variant="caption"
                color={positive ? 'success.main' : 'error.main'}
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}
              >
                {positive ? '▲' : '▼'} {Math.abs(delta)}% {deltaLabel ?? 'vs last period'}
              </Typography>
            )}
          </Box>
          {icon && (
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                bgcolor: (t) => t.palette[color].main + '22',
                color: (t) => t.palette[color].main,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};
