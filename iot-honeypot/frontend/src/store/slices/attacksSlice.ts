import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { attacksApi } from '@/services/api/attacksApi';
import type { Attack, AttackStats } from '@/types/attack';

interface AttacksState {
  recent: Attack[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  stats: AttackStats | null;
}

const initialState: AttacksState = {
  recent: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: false,
  error: null,
  stats: null,
};

export const fetchAttacks = createAsyncThunk<
  { items: Attack[]; total: number },
  { page?: number; pageSize?: number } | undefined
>('attacks/fetch', async (params) => {
  const data = await attacksApi.list(params);
  return { items: data.items, total: data.total };
});

export const fetchStats = createAsyncThunk<AttackStats>('attacks/stats', async () => {
  return attacksApi.stats();
});

const slice = createSlice({
  name: 'attacks',
  initialState,
  reducers: {
    pushLive(state, a: PayloadAction<Attack>) {
      state.recent.unshift(a.payload);
      if (state.recent.length > 200) state.recent.length = 200;
      state.total += 1;
    },
    reset(state) {
      state.recent = [];
      state.total = 0;
    },
    setStats(state, a: PayloadAction<AttackStats>) {
      state.stats = a.payload;
    },
  },
  extraReducers: (b) => {
    b.addCase(fetchAttacks.pending, (s) => {
      s.loading = true;
      s.error = null;
    })
      .addCase(fetchAttacks.fulfilled, (s, a) => {
        s.loading = false;
        s.recent = a.payload.items;
        s.total = a.payload.total;
      })
      .addCase(fetchAttacks.rejected, (s, a) => {
        s.loading = false;
        s.error = a.error.message ?? 'Failed to load attacks';
      })
      .addCase(fetchStats.fulfilled, (s, a) => {
        s.stats = a.payload;
      });
  },
});

export const attacksActions = slice.actions;
export default slice.reducer;