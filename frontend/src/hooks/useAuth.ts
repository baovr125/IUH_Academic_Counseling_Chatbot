import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import * as authService from "../services/authService";
import { queryClient } from "../queryClient";
import type { LoginPayload, RegisterPayload, User } from "../types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<boolean>;
  register: (payload: RegisterPayload) => Promise<{
    ok: boolean;
    message?: string;
    field?: string;
    details?: Array<{ field: string; message: string; type?: string }>;
  }>;
  logout: () => Promise<void>;
  linkGoogleAccount: (idToken: string) => Promise<{ ok: boolean; message?: string; user?: User }>;
  setAccountPassword: (newPassword: string, confirmPassword: string) => Promise<{ ok: boolean; message?: string }>;
  updateProfile: (payload: Partial<User>) => Promise<{ ok: boolean; message?: string; user?: User }>;
  forgotPassword: (email: string) => Promise<{ ok: boolean; message?: string; devOtp?: string }>;
  resetPassword: (payload: { email: string; otp: string; newPassword: string; confirmPassword: string }) => Promise<{ ok: boolean; message?: string }>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Provider wraps the app. It owns the only piece of auth state; every
 * component consumes it through useAuth() rather than calling authService
 * directly, keeping data-fetching out of UI components.
 */
export function useAuthState(): AuthContextValue {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => !!authService.getToken());
  const [error, setError] = useState<string | null>(null);

  // Khôi phục phiên làm việc từ JWT token trong sessionStorage khi khởi động
  useEffect(() => {
    const token = authService.getToken();
    if (token && !user) {
      setIsLoading(true);
      authService
        .fetchCurrentUser()
        .then((result) => {
          if (result.ok && result.data) {
            setUser(result.data);
          } else {
            authService.removeToken();
          }
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [user]);

  const login = useCallback(async (payload: LoginPayload) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.login(payload);
    setIsLoading(false);

    if (!result.ok) {
      setError(result.error.message);
      return false;
    }
    queryClient.clear();
    setUser(result.data.user);
    return true;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.register(payload);
    setIsLoading(false);

    if (!result.ok) {
      const msg = result.error?.message || "Đăng ký không thành công.";
      setError(msg);
      return {
        ok: false,
        message: msg,
        field: result.error?.field,
        details: result.error?.details,
      };
    }
    queryClient.clear();
    return { ok: true };
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    queryClient.clear();
    setUser(null);
  }, []);

  const linkGoogleAccount = useCallback(async (idToken: string) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.linkGoogleAccount(idToken);
    setIsLoading(false);

    if (!result.ok) {
      const msg = result.error.message;
      setError(msg);
      return { ok: false, message: msg };
    }

    setUser(result.data);
    return { ok: true, user: result.data };
  }, []);

  const setAccountPassword = useCallback(async (newPassword: string, confirmPassword: string) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.setAccountPassword(newPassword, confirmPassword);
    setIsLoading(false);

    if (!result.ok) {
      const msg = result.error.message;
      setError(msg);
      return { ok: false, message: msg };
    }

    // Cập nhật indicator cờ mật khẩu vào state người dùng
    setUser((prev) => (prev ? { ...prev, password_hash: "hashed", passwordHash: "hashed" } : prev));
    return { ok: true };
  }, []);

  const updateProfile = useCallback(async (payload: Partial<User>) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.updateProfile(payload);
    setIsLoading(false);

    if (!result.ok) {
      const msg = result.error.message;
      setError(msg);
      return { ok: false, message: msg };
    }

    setUser(result.data);
    return { ok: true, user: result.data };
  }, []);

  const forgotPassword = useCallback(async (email: string) => {
    setIsLoading(true);
    setError(null);
    const result = await authService.forgotPassword(email);
    setIsLoading(false);

    if (!result.ok) {
      const msg = result.error.message;
      setError(msg);
      return { ok: false, message: msg };
    }

    return { ok: true, message: result.data.message, devOtp: result.data.devOtp };
  }, []);

  const resetPassword = useCallback(
    async (payload: { email: string; otp: string; newPassword: string; confirmPassword: string }) => {
      setIsLoading(true);
      setError(null);
      const result = await authService.resetPassword(payload);
      setIsLoading(false);

      if (!result.ok) {
        const msg = result.error.message;
        setError(msg);
        return { ok: false, message: msg };
      }

      return { ok: true };
    },
    []
  );

  const updateUser = useCallback((updated: User) => {
    setUser(updated);
  }, []);

  return useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      error,
      login,
      register,
      logout,
      linkGoogleAccount,
      setAccountPassword,
      updateProfile,
      forgotPassword,
      resetPassword,
      updateUser,
    }),
    [
      user,
      isLoading,
      error,
      login,
      register,
      logout,
      linkGoogleAccount,
      setAccountPassword,
      updateProfile,
      forgotPassword,
      resetPassword,
      updateUser,
    ]
  );
}

export { AuthContext };

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
