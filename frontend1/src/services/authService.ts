import type { ApiResult, AuthResponse, LoginPayload, RegisterPayload, User } from "../types";

const TOKEN_KEY = "iuh_portal_ai_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "").replace(/\/+$/, "");
  if (!base) return endpoint;
  if (base.endsWith("/api") && endpoint.startsWith("/api/")) {
    return `${base}${endpoint.slice(4)}`;
  }
  return `${base}${endpoint}`;
};

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResult<T>> {
  const url = getApiUrl(endpoint);
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const contentType = response.headers.get("content-type") || "";
    let data: any;

    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      const text = await response.text();
      return {
        ok: false,
        error: {
          message: response.ok
            ? "Máy chủ trả về định dạng không phải JSON."
            : `Lỗi kết nối máy chủ (${response.status}): ${response.statusText || text.slice(0, 80)}`,
          code: String(response.status),
        },
      };
    }

    if (!response.ok || data.ok === false) {
      let errorMessage = "Yêu cầu đến máy chủ thất bại.";
      if (data?.error?.message && typeof data.error.message === "string") {
        errorMessage = data.error.message;
      } else if (typeof data?.detail === "string") {
        errorMessage = data.detail;
      } else if (Array.isArray(data?.detail)) {
        errorMessage = data.detail
          .map((item: any) => (typeof item === "string" ? item : item?.msg || JSON.stringify(item)))
          .join("; ");
      } else if (data?.message && typeof data.message === "string") {
        errorMessage = data.message;
      }

      return {
        ok: false,
        error: {
          message: errorMessage,
          code: String(response.status),
        },
      };
    }

    return {
      ok: true,
      data: data.data !== undefined ? data.data : data,
    };
  } catch (error: any) {
    return {
      ok: false,
      error: {
        message: error?.message || "Không thể kết nối đến máy chủ.",
      },
    };
  }
}

export async function login(payload: LoginPayload): Promise<ApiResult<AuthResponse>> {
  const result = await request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (result.ok && result.data?.token) {
    setToken(result.data.token);
  }

  return result;
}

export async function register(payload: RegisterPayload): Promise<ApiResult<AuthResponse>> {
  const result = await request<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (result.ok && result.data?.token) {
    setToken(result.data.token);
  }

  return result;
}

export async function logout(): Promise<ApiResult<null>> {
  removeToken();
  return { ok: true, data: null };
}

export async function fetchCurrentUser(): Promise<ApiResult<User>> {
  const token = getToken();
  if (!token) {
    return {
      ok: false,
      error: { message: "Chưa đăng nhập hệ thống." },
    };
  }

  return await request<User>("/api/auth/me", {
    method: "GET",
  });
}

export async function linkGoogleAccount(idToken: string): Promise<ApiResult<User>> {
  return await request<User>("/api/auth/link-google", {
    method: "POST",
    body: JSON.stringify({ idToken }),
  });
}

export async function setAccountPassword(
  newPassword: string,
  confirmPassword: string
): Promise<ApiResult<null>> {
  return await request<null>("/api/auth/set-password", {
    method: "POST",
    body: JSON.stringify({ newPassword, confirmPassword }),
  });
}

export async function updateProfile(payload: Partial<User>): Promise<ApiResult<User>> {
  return await request<User>("/api/auth/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function forgotPassword(
  email: string
): Promise<ApiResult<{ message: string; devOtp?: string }>> {
  return await request<{ message: string; devOtp?: string }>("/api/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(payload: {
  email: string;
  otp: string;
  newPassword: string;
  confirmPassword: string;
}): Promise<ApiResult<null>> {
  return await request<null>("/api/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
