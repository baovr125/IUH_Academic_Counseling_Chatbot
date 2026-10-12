import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import * as authService from "../services/authService";
import { setUnauthorizedHandler } from "../services/apiClient";
import { queryClient } from "../queryClient";
import type {
  ApiError,
  ChangePasswordPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  User,
} from "../types";

interface ActionResult {
  ok: boolean;
  message?: string;
  field?: string;
  details?: ApiError["details"];
}

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<boolean>;
  register: (payload: RegisterPayload) => Promise<ActionResult>;
  logout: () => Promise<void>;
  updateProfile: (payload: UpdateProfilePayload) => Promise<ActionResult & { user?: User }>;
  changePassword: (payload: ChangePasswordPayload) => Promise<ActionResult>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/** Làm mới token khi còn chừng này mili-giây trước lúc hết hạn. */
const REFRESH_BEFORE_EXPIRY_MS = 5 * 60 * 1000;
const MAX_TIMER_MS = 2 ** 31 - 1;

/**
 * Provider wraps the app. It owns the only piece of auth state; every
 * component consumes it through useAuth() rather than calling authService
 * directly, keeping data-fetching out of UI components.
 */
export function useAuthState(): AuthContextValue {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => !!authService.getToken());
  const [error, setError] = useState<string | null>(null);
  const hasUser = user !== null;
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearSession = useCallback(() => {
    authService.removeToken();
    queryClient.clear();
    setUser(null);
  }, []);

  // Khôi phục phiên từ token đã lưu khi khởi động.
  useEffect(() => {
    if (!authService.getToken()) {
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    authService
      .fetchCurrentUser()
      .then((result) => {
        if (cancelled) return;
        if (result.ok) {
          setUser(result.data);
        } else if (result.error.code === "401" || result.error.code === "403") {
          authService.removeToken(); // token hết hạn/bị thu hồi
        }
        // Lỗi mạng/503: giữ token để lần tải sau thử lại, nhưng chưa coi là đã đăng nhập.
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Mọi API trả 401 khi đang có token => đăng xuất đồng bộ trên toàn ứng dụng.
  useEffect(() => {
    setUnauthorizedHandler(clearSession);
    return () => setUnauthorizedHandler(null);
  }, [clearSession]);

  // Đồng bộ đa tab: tab khác đăng xuất (xóa token) thì tab này cũng đăng xuất.
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "iuh_portal_ai_token" && !authService.getToken()) {
        queryClient.clear();
        setUser(null);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // Tự làm mới access token trước khi hết hạn; thất bại vì 401 thì đăng xuất.
  useEffect(() => {
    if (!hasUser) return;

    const refreshNow = async () => {
      const result = await authService.refreshSession();
      if (result.ok) {
        setUser(result.data.user);
      } else if (result.error.code === "401") {
        clearSession();
      }
    };

    const schedule = () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      const exp = authService.getTokenExpiry();
      if (!exp) return;
      const delay = Math.min(Math.max(exp - Date.now() - REFRESH_BEFORE_EXPIRY_MS, 0), MAX_TIMER_MS);
      refreshTimer.current = setTimeout(async () => {
        await refreshNow();
        schedule();
      }, delay);
    };
    schedule();

    // Máy ngủ/tab nền làm setTimeout trễ: kiểm tra lại khi người dùng quay lại tab.
    const onVisible = () => {
      if (document.visibilityState !== "visible") return;
      const exp = authService.getTokenExpiry();
      if (exp && exp - Date.now() < REFRESH_BEFORE_EXPIRY_MS) {
        void refreshNow().then(schedule);
      }
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [hasUser, clearSession]);

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

  const register = useCallback(async (payload: RegisterPayload): Promise<ActionResult> => {
    setIsLoading(true);
    setError(null);
    const result = await authService.register(payload);
    setIsLoading(false);

    if (!result.ok) {
      const msg = result.error.message || "Đăng ký không thành công.";
      setError(msg);
      return { ok: false, message: msg, field: result.error.field, details: result.error.details };
    }
    // Không tự đăng nhập: người dùng đăng nhập lại để chắc chắn đúng tài khoản vừa tạo.
    authService.removeToken();
    return { ok: true };
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    queryClient.clear();
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (payload: UpdateProfilePayload) => {
    setError(null);
    const result = await authService.updateProfile(payload);
    if (!result.ok) {
      return { ok: false, message: result.error.message, field: result.error.field };
    }
    setUser(result.data);
    return { ok: true, user: result.data };
  }, []);

  const changePassword = useCallback(async (payload: ChangePasswordPayload): Promise<ActionResult> => {
    setError(null);
    const result = await authService.changePassword(payload);
    if (!result.ok) {
      return { ok: false, message: result.error.message, field: result.error.field };
    }
    setUser(result.data.user);
    return { ok: true };
  }, []);

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
      updateProfile,
      changePassword,
      updateUser,
    }),
    [user, isLoading, error, login, register, logout, updateProfile, changePassword, updateUser]
  );
}

export { AuthContext };

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
