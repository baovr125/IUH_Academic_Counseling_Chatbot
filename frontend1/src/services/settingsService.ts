import type { ApiResult, UserSettings, UpdateSettingsPayload } from "../types";
import { getToken } from "./authService";

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
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

    const data = await response.json();

    if (!response.ok || data.ok === false) {
      let errorMessage = "Yêu cầu đến máy chủ thất bại.";
      if (data?.error?.message && typeof data.error.message === "string") {
        errorMessage = data.error.message;
      } else if (typeof data?.detail === "string") {
        errorMessage = data.detail;
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

export async function fetchUserSettings(): Promise<ApiResult<UserSettings>> {
  return await request<UserSettings>("/api/settings", {
    method: "GET",
  });
}

export async function updateUserSettings(
  payload: UpdateSettingsPayload
): Promise<ApiResult<UserSettings>> {
  return await request<UserSettings>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
