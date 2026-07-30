import React, { useEffect } from 'react';
import { Card, CardContent, Box } from '@mui/material';
import { PageHeader } from '@/components/common/PageHeader';
import { usePageTitle } from '@/hooks/usePageTitle';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAlerts } from '@/store/slices/alertsSlice';
import { AlertsList } from '@/components/tables/AlertsList';

export const AlertsPage: React.FC = () => {
  usePageTitle('Alerts');
  const dispatch = useAppDispatch();
  const items = useAppSelector((s) => s.alerts.items);

  useEffect(() => {
    dispatch(fetchAlerts()).catch(() => {});
  }, [dispatch]);

  return (
    <Box>
      <PageHeader
        title="Alerts"
        subtitle={`${items.length} alerts · ${items.filter((i) => !i.acknowledged).length} unread`}
      />
      <Card>
        <CardContent sx={{ p: 0 }}>
          <AlertsList items={items} />
        </CardContent>
      </Card>
    </Box>
  );
};