import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

export const formatDate = (d: string | Date | undefined | null, withTime = true): string => {
  if (!d) return '—';
  const fmt = withTime ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD';
  return dayjs(d).format(fmt);
};

export const fromNow = (d: string | Date | undefined | null): string => {
  if (!d) return '—';
  return dayjs(d).fromNow();
};

export const compactNumber = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
};

export const severityColor = (s: string): 'success' | 'info' | 'warning' | 'error' => {
  switch (s) {
    case 'low':
      return 'info';
    case 'medium':
      return 'warning';
    case 'high':
      return 'error';
    case 'critical':
      return 'error';
    default:
      return 'info';
  }
};