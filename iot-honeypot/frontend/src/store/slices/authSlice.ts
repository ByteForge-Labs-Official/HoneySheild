import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { authApi } from '@/services/api/authApi';
import { tokenStorage } from '@/services/storage/tokenStorage';
import type { AuthUser, LoginCredentials, TokenPair } from '@/types/auth';

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: Boolean(tokenStorage.getAccessToken()),
  status: 'idle',
  error: null,
};

export const loginThunk = createAsyncThunk<
  { user: AuthUser; tokens: TokenPair },
  LoginCredentials,
  { rejectValue: string }
>('auth/login', async (creds, { rejectWithValue }) => {
  try {
    const tokens = await authApi.login(creds);
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
    const user = await authApi.me();
    return { user, tokens };
  } catch (e) {
    const msg =
      (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
      'Login failed';
    return rejectWithValue(msg);
  }
});

export const refreshThunk = createAsyncThunk<
  TokenPair,
  void,
  { rejectValue: string }
>('auth/refresh', async (_, { rejectWithValue }) => {
  const refresh = tokenStorage.getRefreshToken();
  if (!refresh) return rejectWithValue('No refresh token');
  try {
    const tokens = await authApi.refresh(refresh);
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
    return tokens;
  } catch {
    tokenStorage.clear();
    return rejectWithValue('Refresh failed');
  }
});

export const logoutThunk = createAsyncThunk<void, void>('auth/logout', async () => {
  try {
    await authApi.logout();
  } finally {
    tokenStorage.clear();
  }
});

const slice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (b) => {
    b.addCase(loginThunk.pending, (s) => {
      s.status = 'loading';
      s.error = null;
    })
      .addCase(loginThunk.fulfilled, (s, a: PayloadAction<{ user: AuthUser }>) => {
        s.status = 'succeeded';
        s.isAuthenticated = true;
        s.user = a.payload.user;
      })
      .addCase(loginThunk.rejected, (s, a) => {
        s.status = 'failed';
        s.error = a.payload ?? 'Login failed';
      })
      .addCase(logoutThunk.fulfilled, (s) => {
        s.user = null;
        s.isAuthenticated = false;
        s.status = 'idle';
      });
  },
});

export const { clearError } = slice.actions;
export default slice.reducer;