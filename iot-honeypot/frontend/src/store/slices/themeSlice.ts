import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { ThemeMode } from '@/theme/theme';

interface ThemeState {
  mode: ThemeMode;
}

const STORAGE_KEY = 'honeynet.theme';

function getInitial(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    /* noop */
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

const initialState: ThemeState = { mode: getInitial() };

const slice = createSlice({
  name: 'theme',
  initialState,
  reducers: {
    toggle(state) {
      state.mode = state.mode === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem(STORAGE_KEY, state.mode);
      } catch {
        /* noop */
      }
    },
    set(state, a: PayloadAction<ThemeMode>) {
      state.mode = a.payload;
      try {
        localStorage.setItem(STORAGE_KEY, state.mode);
      } catch {
        /* noop */
      }
    },
  },
});

export const themeActions = slice.actions;
export default slice.reducer;