import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import themeReducer from './slices/themeSlice';
import attacksReducer from './slices/attacksSlice';
import alertsReducer from './slices/alertsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    theme: themeReducer,
    attacks: attacksReducer,
    alerts: alertsReducer,
  },
  middleware: (getDefault) =>
    getDefault({
      serializableCheck: {
        // Allow Date objects inside attack payloads (e.g. timestamp).
        ignoredActionPaths: ['payload.timestamp', 'payload.lastSeen'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;