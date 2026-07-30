import React, { useEffect, useState } from 'react';
import { Card, CardContent, Stack, MenuItem, TextField, Box } from '@mui/material';
import { PageHeader } from '@/components/common/PageHeader';
import { usePageTitle } from '@/hooks/usePageTitle';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAttacks } from '@/store/slices/attacksSlice';
import { AttacksTable } from '@/components/tables/AttacksTable';

export const AttacksPage: React.FC = () => {
  usePageTitle('Attacks');
  const dispatch = useAppDispatch();
  const { recent, loading, total } = useAppSelector((s) => s.attacks);
  const [severity, setSeverity] = useState('');
  const [protocol, setProtocol] = useState('');

  useEffect(() => {
    dispatch(fetchAttacks({ page: 1, pageSize: 100 }));
  }, [dispatch]);

  const filtered = recent.filter(
    (a) =>
      (!severity || a.severity === severity) &&
      (!protocol || a.protocol === protocol),
  );

  return (
    <Box>
      <PageHeader
        title="Attack log"
        subtitle={`${total.toLocaleString()} attacks captured`}
        actions={
          <Stack direction="row" spacing={2}>
            <TextField
              select
              size="small"
              label="Protocol"
              value={protocol}
              onChange={(e) => setProtocol(e.target.value)}
              sx={{ minWidth: 140 }}
            >
              <MenuItem value="">All</MenuItem>
              {['ssh', 'telnet', 'http', 'rtsp', 'mqtt', 'modbus', 'upnp'].map((p) => (
                <MenuItem key={p} value={p}>
                  {p.toUpperCase()}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label="Severity"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              sx={{ minWidth: 140 }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </TextField>
          </Stack>
        }
      />

      <Card>
        <CardContent>
          <AttacksTable rows={filtered} loading={loading} />
        </CardContent>
      </Card>
    </Box>
  );
};