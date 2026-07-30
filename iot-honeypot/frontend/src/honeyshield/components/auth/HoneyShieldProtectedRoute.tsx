import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

/**
 * SOC auth gate. The SOC dashboard is demo-first; auth is opt-in via the
 * BackendStatusBanner sign-in flow. Protected routes are pass-through so deep
 * links resolve even before the user authenticates.
 */
export function HoneyShieldProtectedRoute({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

/**
 * Reverse gate: send already-authed users away from /login to the dashboard.
 */
export function HoneyShieldPublicRoute({ children }: { children: ReactNode }) {
  const location = useLocation();
  const authed =
    typeof window !== 'undefined' &&
    Boolean(window.localStorage.getItem('hs_access_token'));
  if (authed) {
    const from =
      (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/';
    return <Navigate to={from} replace />;
  }
  return <>{children}</>;
}
