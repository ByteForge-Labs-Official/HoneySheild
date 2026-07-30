import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

export const LoadingScreen: React.FC<{ label?: string }> = ({ label = 'Loading…' }) => (
  <Box
    sx={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 2,
    }}
  >
    <CircularProgress />
    <Typography color="text.secondary">{label}</Typography>
  </Box>
);
