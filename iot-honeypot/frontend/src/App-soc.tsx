import { Navigate, Route, Routes } from 'react-router-dom';
import HoneyShieldPage from './pages/HoneyShieldPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HoneyShieldPage />} />
      <Route path="/honeyshield" element={<HoneyShieldPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
