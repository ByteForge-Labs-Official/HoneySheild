import React from 'react';
import { Chip, type ChipProps } from '@mui/material';
import type { AttackSeverity } from '@/types/attack';

const COLORS: Record<AttackSeverity, ChipProps['color']> = {
  low: 'info',
  medium: 'warning',
  high: 'error',
  critical: 'error',
};

export const SeverityBadge: React.FC<{ severity: AttackSeverity }> = ({ severity }) => (
  <Chip
    label={severity.toUpperCase()}
    size="small"
    color={COLORS[severity]}
    variant={severity === 'critical' ? 'filled' : 'outlined'}
    sx={{ fontWeight: 600, letterSpacing: 0.5 }}
  />
);
