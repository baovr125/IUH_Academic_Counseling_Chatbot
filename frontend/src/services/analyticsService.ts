import type { ApiResult, AnalyticsData } from "../types";
import { getToken } from "./authService";

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "").replace(/\/+$/, "");
  if (!base) return endpoint;
  if (base.endsWith("/api") && endpoint.startsWith("/api/")) {
    return `${base}${endpoint.slice(4)}`;
  }
  return `${base}${endpoint}`;
};

function getAuthHeaders(): Record<string, string> {
  const token = getToken() || localStorage.getItem("token") || localStorage.getItem("auth_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchAnalyticsOverview(): Promise<ApiResult<AnalyticsData>> {
  try {
    const res = await fetch(getApiUrl("/api/analytics/overview"), {
      method: "GET",
      headers: getAuthHeaders(),
    });

    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return {
        ok: false,
        error: { message: `Lỗi máy chủ (${res.status}): Không thể kết nối Backend API.` },
      };
    }

    const result = await res.json();
    return result;
  } catch (err: any) {
    return {
      ok: false,
      error: { message: err.message || "Lỗi kết nối tới Server Backend." },
    };
  }
}
