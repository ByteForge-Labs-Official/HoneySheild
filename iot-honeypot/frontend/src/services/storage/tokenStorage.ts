const ACCESS_KEY = 'honeynet.access';
const REFRESH_KEY = 'honeynet.refresh';

export const tokenStorage = {
  getAccessToken(): string | null {
    try {
      return localStorage.getItem(ACCESS_KEY);
    } catch {
      return null;
    }
  },
  getRefreshToken(): string | null {
    try {
      return localStorage.getItem(REFRESH_KEY);
    } catch {
      return null;
    }
  },
  setTokens(access: string, refresh: string): void {
    try {
      localStorage.setItem(ACCESS_KEY, access);
      localStorage.setItem(REFRESH_KEY, refresh);
    } catch {
      /* noop */
    }
  },
  setAccess(access: string): void {
    try {
      localStorage.setItem(ACCESS_KEY, access);
    } catch {
      /* noop */
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      /* noop */
    }
  },
};