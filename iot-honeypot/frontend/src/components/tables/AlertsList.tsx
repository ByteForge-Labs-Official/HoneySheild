import React from 'react';
import {
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Typography,
  Box,
  IconButton,
  Chip,
  Divider,
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import dayjs from 'dayjs';

import type { Alert } from '@/types/alert';
import { useAppDispatch } from '@/store/hooks';
import { alertsActions } from '@/store/slices/alertsSlice';
import { alertsApi } from '@/services/api/alertsApi';

const ICONS: Record<string, React.ReactNode> = {
  low: <InfoIcon />,
  medium: <WarningIcon />,
  high: <ErrorIcon />,
  critical: <ErrorIcon />,
};

const COLORS: Record<string, string> = {
  low: 'info.main',
  medium: 'warning.main',
  high: 'error.main',
  critical: 'error.main',
};

export const AlertsList: React.FC<{ items: Alert[] }> = ({ items }) => {
  const dispatch = useAppDispatch();

  const acknowledge = async (id: string) => {
    try {
      const updated = await alertsApi.acknowledge(id);
      dispatch(alertsActions.acknowledge(updated.id));
    } catch {
      dispatch(alertsActions.acknowledge(id));
    }
  };

  if (items.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="text.secondary">No alerts.</Typography>
      </Box>
    );
  }

  return (
    <List disablePadding>
      {items.map((a, idx) => (
        <Box key={a.id}>
          <ListItem
            sx={{
              bgcolor: a.acknowledged ? 'transparent' : 'action.hover',
              alignItems: 'flex-start',
              py: 2,
            }}
            secondaryAction={
              !a.acknowledged && (
                <IconButton edge="end" onClick={() => acknowledge(a.id)}>
                  <CheckIcon />
                </IconButton>
              )
            }
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: COLORS[a.severity] ?? 'primary.main' }}>
                {ICONS[a.severity] ?? <InfoIcon />}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {a.title}
                  </Typography>
                  <Chip
                    label={a.severity.toUpperCase()}
                    size="small"
                    color={a.severity === 'critical' ? 'error' : 'default'}
                    variant="outlined"
                  />
                </Box>
              }
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.secondary">
                    {a.description}
                  </Typography>
                  <br />
                  <Typography component="span" variant="caption" color="text.secondary">
                    {dayjs(a.created_at).format('YYYY-MM-DD HH:mm:ss')}
                    {a.source_ip ? ` · ${a.source_ip}` : ''}
                  </Typography>
                </>
              }
            />
          </ListItem>
          {idx < items.length - 1 && <Divider component="li" />}
        </Box>
      ))}
    </List>
  );
};