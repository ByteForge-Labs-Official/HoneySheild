import React, { useMemo } from 'react';
import {
  DataGrid,
  type GridColDef,
  type GridRowParams,
} from '@mui/x-data-grid';
import { Box } from '@mui/material';
import dayjs from 'dayjs';
import type { Attack } from '@/types/attack';
import { SeverityBadge } from '@/components/common/SeverityBadge';

interface AttacksTableProps {
  rows: Attack[];
  loading?: boolean;
  pageSize?: number;
  onRowClick?: (attack: Attack) => void;
}

export const AttacksTable: React.FC<AttacksTableProps> = ({
  rows,
  loading,
  pageSize = 20,
  onRowClick,
}) => {
  const columns = useMemo<GridColDef<Attack>[]>(
    () => [
      {
        field: 'timestamp',
        headerName: 'Time',
        width: 180,
        valueFormatter: (v: string) =>
          v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '—',
      },
      { field: 'source_ip', headerName: 'Source IP', width: 140 },
      {
        field: 'protocol',
        headerName: 'Protocol',
        width: 110,
        valueFormatter: (v: string) => (v ? v.toUpperCase() : '—'),
      },
      { field: 'honeypot_name', headerName: 'Honeypot', width: 140 },
      { field: 'country', headerName: 'Country', width: 90 },
      {
        field: 'severity',
        headerName: 'Severity',
        width: 130,
        renderCell: (p) => <SeverityBadge severity={p.value as Attack['severity']} />,
      },
      {
        field: 'mitre_tags',
        headerName: 'MITRE',
        width: 140,
        renderCell: (p) =>
          Array.isArray(p.value) && p.value.length > 0
            ? p.value.join(', ')
            : '—',
      },
      { field: 'payload_summary', headerName: 'Payload', flex: 1, minWidth: 200 },
    ],
    [],
  );

  return (
    <Box sx={{ height: 560, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        loading={loading}
        pageSizeOptions={[10, 20, 50, 100]}
        initialState={{
          pagination: { paginationModel: { pageSize, page: 0 } },
        }}
        disableRowSelectionOnClick
        onRowClick={(p: GridRowParams<Attack>) => onRowClick?.(p.row)}
        sx={{
          border: 'none',
          '& .MuiDataGrid-cell:focus': { outline: 'none' },
          '& .MuiDataGrid-row:hover': { cursor: 'pointer' },
        }}
      />
    </Box>
  );
};