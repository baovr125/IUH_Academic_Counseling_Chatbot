import { createContext, useCallback, useContext, useMemo, useState } from "react";
import * as authService from "../services/authService";
import type { LoginPayload, RegisterPayload, User } from "../types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<boolean>;
  register: (payload: RegisterPayload) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Provider wraps the app. It owns the only piece of auth state; every
 * component consumes it through useAuth() rather than calling authService
 * directly, keeping data-fetching out of UI components.
 */
export function useAuthState(): AuthContextValue {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (payload: LoginPayload) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.login(payload);
    setIsLoading(false);

    if (!result.ok) {
      setError(result.error.message);
      return false;
    }
    setUser(result.data.user);
    return true;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.register(payload);
    setIsLoading(false);

    if (!result.ok) {
      setError(result.error.message);
      return false;
    }
    setUser(result.data.user);
    return true;
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  return useMemo(
    () => ({ user, isAuthenticated: !!user, isLoading, error, login, register, logout }),
    [user, isLoading, error, login, register, logout]
  );
}

export { AuthContext };

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
