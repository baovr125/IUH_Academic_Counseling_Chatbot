import type {
  ApiResult,
  AuthResponse,
  ChangePasswordPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  User,
} from "../types";
import { getToken, isTokenRemembered, removeToken, request, setToken } from "./apiClient";

// Giữ các hàm quản lý token ở một nơi (apiClient) nhưng vẫn xuất lại để mã cũ import từ authService.
export { getToken, getTokenExpiry, isTokenRemembered, removeToken, setToken } from "./apiClient";

export async function login(payload: LoginPayload): Promise<ApiResult<AuthResponse>> {
  const { rememberMe, ...body } = payload;
  const result = await request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (result.ok && result.data?.token) {
    setToken(result.data.token, Boolean(rememberMe));
  }
  return result;
}

export async function register(payload: RegisterPayload): Promise<ApiResult<AuthResponse>> {
  return request<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Thu hồi token phía server (nếu server hỗ trợ) rồi xóa token ở client; luôn đăng xuất được kể cả khi mạng lỗi. */
export async function logout(): Promise<ApiResult<null>> {
  if (getToken()) {
    try {
      await request<{ revoked: boolean }>("/api/auth/logout", { method: "POST" });
    } catch {
      /* đăng xuất cục bộ vẫn tiếp tục */
    }
  }
  removeToken();
  return { ok: true, data: null };
}

export async function fetchCurrentUser(): Promise<ApiResult<User>> {
  if (!getToken()) {
    return { ok: false, error: { message: "Chưa đăng nhập hệ thống.", code: "401" } };
  }
  return request<User>("/api/auth/me", { method: "GET" });
}

/** Đổi lấy access token mới trước khi token cũ hết hạn (giữ nguyên kiểu lưu "ghi nhớ"). */
export async function refreshSession(): Promise<ApiResult<AuthResponse>> {
  const remembered = isTokenRemembered();
  const result = await request<AuthResponse>("/api/auth/refresh", { method: "POST" });
  if (result.ok && result.data?.token) {
    setToken(result.data.token, remembered);
  }
  return result;
}

export async function updateProfile(payload: UpdateProfilePayload): Promise<ApiResult<User>> {
  return request<User>("/api/auth/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: ChangePasswordPayload): Promise<ApiResult<AuthResponse>> {
  const result = await request<AuthResponse>("/api/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (result.ok && result.data?.token) {
    setToken(result.data.token, isTokenRemembered());
  }
  return result;
}
