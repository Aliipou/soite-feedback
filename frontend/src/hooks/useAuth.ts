import { useState, useCallback, useEffect } from "react";
import axios from "axios";
import { login as apiLogin, logout as apiLogout } from "../api/admin";
import { setAccessToken, clearAccessToken, hasAccessToken } from "../auth/tokenStore";

type Role = "staff" | "admin" | null;

interface AuthState {
  isAuthenticated: boolean;
  role: Role;
  loading: boolean;
  error: string | null;
  initializing: boolean;
}

interface UseAuthResult extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

function parseRole(token: string): Role {
  try {
    const payload = JSON.parse(atob(token.split(".")[1])) as { role?: string };
    if (payload.role === "admin" || payload.role === "staff") return payload.role;
  } catch {
    // malformed token — treat as anonymous
  }
  return null;
}

export function useAuth(): UseAuthResult {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: hasAccessToken(),
    role: null,
    loading: false,
    error: null,
    initializing: !hasAccessToken(),
  });

  // On mount: if no access token in memory, try a silent refresh via httpOnly cookie.
  // This handles the page-refresh case without forcing users to log in again.
  useEffect(() => {
    if (hasAccessToken()) {
      setState((s) => ({ ...s, initializing: false }));
      return;
    }

    let cancelled = false;
    const tryRefresh = async () => {
      try {
        const { data } = await axios.post<{ access_token: string }>(
          "/api/v1/auth/refresh",
          {},
          { withCredentials: true }
        );
        if (cancelled) return;
        setAccessToken(data.access_token);
        setState({
          isAuthenticated: true,
          role: parseRole(data.access_token),
          loading: false,
          error: null,
          initializing: false,
        });
      } catch {
        if (cancelled) return;
        setState((s) => ({ ...s, initializing: false }));
      }
    };

    void tryRefresh();
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const { access_token } = await apiLogin(email, password);
      setAccessToken(access_token);
      setState({
        isAuthenticated: true,
        role: parseRole(access_token),
        loading: false,
        error: null,
        initializing: false,
      });
      return true;
    } catch {
      setState((s) => ({
        ...s,
        loading: false,
        error: "Väärä sähköpostiosoite tai salasana",
        initializing: false,
      }));
      return false;
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiLogout();
    } finally {
      clearAccessToken();
      setState({ isAuthenticated: false, role: null, loading: false, error: null, initializing: false });
    }
  }, []);

  return { ...state, login, logout };
}
