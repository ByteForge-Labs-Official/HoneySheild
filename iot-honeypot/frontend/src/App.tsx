import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import { useAppSelector } from './store/hooks';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { LiveMapPage } from './pages/LiveMapPage';
import { StatisticsPage } from './pages/StatisticsPage';
import { AttacksPage } from './pages/AttacksPage';
import { AlertsPage } from './pages/AlertsPage';
import { SettingsPage } from './pages/SettingsPage';

const App: React.FC = () => {
  const isAuthed = useAppSelector((s) => s.auth.isAuthenticated);

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthed ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/live-map" element={<LiveMapPage />} />
        <Route path="/statistics" element={<StatisticsPage />} />
        <Route path="/attacks" element={<AttacksPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;