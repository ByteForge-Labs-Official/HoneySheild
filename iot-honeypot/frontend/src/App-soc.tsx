import { Navigate, Route, Routes } from 'react-router-dom';
import HoneyShieldPage from './pages/HoneyShieldPage';
import { LoginPage } from './honeyshield/page/LoginPage';
import { SettingsPage } from './honeyshield/page/SettingsPage';
import {
  HoneyShieldProtectedRoute,
  HoneyShieldPublicRoute,
} from './honeyshield/components/auth/HoneyShieldProtectedRoute';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HoneyShieldPage />} />
      <Route path="/honeyshield" element={<HoneyShieldPage />} />
      <Route
        path="/login"
        element={
          <HoneyShieldPublicRoute>
            <LoginPage />
          </HoneyShieldPublicRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <HoneyShieldProtectedRoute>
            <SettingsPage />
          </HoneyShieldProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
