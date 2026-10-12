import type { ApiResult, UserSettings, UpdateSettingsPayload } from "../types";
import { getToken, request } from "./apiClient";

export async function fetchUserSettings(): Promise<ApiResult<UserSettings>> {
  const token = getToken();
  if (!token) {
    return {
      ok: false,
      error: { message: "Người dùng chưa đăng nhập.", code: "401" },
    };
  }
  return await request<UserSettings>("/api/auth/settings", {
    method: "GET",
  });
}

export async function updateUserSettings(
  payload: UpdateSettingsPayload
): Promise<ApiResult<UserSettings>> {
  const token = getToken();
  if (!token) {
    return {
      ok: false,
      error: { message: "Người dùng chưa đăng nhập.", code: "401" },
    };
  }
  return await request<UserSettings>("/api/auth/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

