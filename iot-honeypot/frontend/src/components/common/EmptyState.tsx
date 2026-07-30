import React from 'react';
import { Card, CardContent, Stack, Typography, Button } from '@mui/material';
import InboxIcon from '@mui/icons-material/Inbox';

interface EmptyStateProps {
  title: string;
  message?: string;
  action?: { label: string; onClick: () => void };
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, message, action, icon }) => (
  <Card variant="outlined">
    <CardContent>
      <Stack alignItems="center" spacing={2} sx={{ py: 6, textAlign: 'center' }}>
        <Stack
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            bgcolor: (t) => t.palette.action.hover,
            color: 'text.secondary',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon ?? <InboxIcon fontSize="large" />}
        </Stack>
        <Typography variant="h6">{title}</Typography>
        {message && <Typography color="text.secondary">{message}</Typography>}
        {action && <Button variant="contained" onClick={action.onClick}>{action.label}</Button>}
      </Stack>
    </CardContent>
  </Card>
);
