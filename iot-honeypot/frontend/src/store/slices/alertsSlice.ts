import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { alertsApi } from '@/services/api/alertsApi';
import type { Alert } from '@/types/alert';

interface AlertsState {
  items: Alert[];
  unread: number;
  loading: boolean;
  error: string | null;
}

const initialState: AlertsState = {
  items: [],
  unread: 0,
  loading: false,
  error: null,
};

export const fetchAlerts = createAsyncThunk<Alert[]>('alerts/fetch', async () => {
  return alertsApi.list();
});

const slice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    acknowledge(state, a: { payload: string }) {
      const it = state.items.find((x) => x.id === a.payload);
      if (it) it.acknowledged = true;
      state.unread = state.items.filter((x) => !x.acknowledged).length;
    },
    pushLive(state, a: { payload: Alert }) {
      state.items.unshift(a.payload);
      if (!a.payload.acknowledged) state.unread += 1;
      if (state.items.length > 100) state.items.length = 100;
    },
  },
  extraReducers: (b) => {
    b.addCase(fetchAlerts.pending, (s) => {
      s.loading = true;
      s.error = null;
    })
      .addCase(fetchAlerts.fulfilled, (s, a) => {
        s.loading = false;
        s.items = a.payload;
        s.unread = a.payload.filter((x) => !x.acknowledged).length;
      })
      .addCase(fetchAlerts.rejected, (s, a) => {
        s.loading = false;
        s.error = a.error.message ?? 'Failed to load alerts';
      });
  },
});

export const alertsActions = slice.actions;
export default slice.reducer;