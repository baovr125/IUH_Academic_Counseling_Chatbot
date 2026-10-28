import type { ApiResult } from "../types";
import { getApiBaseUrl } from "../config";

const TOKEN_KEY = "iuh_portal_ai_token";

// ---- Lưu token ------------------------------------------------------------
// "Ghi nhớ đăng nhập" => localStorage (sống qua việc đóng trình duyệt/mở tab mới);
// mặc định => sessionStorage (chỉ trong tab hiện tại).
function safeGet(storage: Storage, key: string): string | null {
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return safeGet(sessionStorage, TOKEN_KEY) ?? safeGet(localStorage, TOKEN_KEY);
}

export function isTokenRemembered(): boolean {
  return safeGet(localStorage, TOKEN_KEY) !== null && safeGet(sessionStorage, TOKEN_KEY) === null;
}

export function setToken(token: string, remember: boolean = isTokenRemembered()): void {
  removeToken();
  try {
    (remember ? localStorage : sessionStorage).setItem(TOKEN_KEY, token);
  } catch {
    /* Trình duyệt chặn storage: phiên chỉ sống trong bộ nhớ trang (user sẽ phải đăng nhập lại khi tải lại). */
  }
}

export function removeToken(): void {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

/** Thời điểm hết hạn (ms epoch) đọc từ claim `exp` của JWT; null nếu không đọc được. */
export function getTokenExpiry(token: string | null = getToken()): number | null {
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    const json = atob(part.replace(/-/g, "+").replace(/_/g, "/"));
    const exp = JSON.parse(json).exp;
    return typeof exp === "number" ? exp * 1000 : null;
  } catch {
    return null;
  }
}

// ---- URL ------------------------------------------------------------------
export const getApiUrl = (endpoint: string): string => {
  const base = getApiBaseUrl();
  if (!base) return endpoint;
  if (base.endsWith("/api") && endpoint.startsWith("/api/")) {
    return `${base}${endpoint.slice(4)}`;
  }
  return `${base}${endpoint}`;
};

// ---- Hết phiên (401) -------------------------------------------------------
type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

// Các endpoint mà 401/lỗi là kết quả bình thường của form, không phải "phiên hết hạn".
const FORM_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/change-password"];

function isFormEndpoint(url: string): boolean {
  return FORM_ENDPOINTS.some((p) => url.includes(p));
}

let interceptorInstalled = false;

/**
 * Bọc window.fetch một lần: mọi lời gọi tới API mà có gắn token hiện tại và nhận 401
 * (token hết hạn/bị thu hồi) sẽ đưa ứng dụng về trạng thái đăng xuất, thay vì để từng
 * trang tự xử lý rời rạc.
 */
export function installAuthFetchInterceptor(): void {
  if (interceptorInstalled || typeof window === "undefined" || typeof window.fetch !== "function") return;
  interceptorInstalled = true;
  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const response = await originalFetch(input, init);
    if (response.status === 401) {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const headers = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined));
      const sentToken = headers.get("Authorization");
      const current = getToken();
      if (current && sentToken === `Bearer ${current}` && url.includes("/api/") && !isFormEndpoint(url)) {
        unauthorizedHandler?.();
      }
    }
    return response;
  };
}

// ---- Gọi API --------------------------------------------------------------
export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResult<T>> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const response = await fetch(getApiUrl(endpoint), { ...options, headers });
    const contentType = response.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {
      return {
        ok: false,
        error: {
          message: response.ok
            ? "Máy chủ trả về định dạng không phải JSON."
            : `Lỗi kết nối máy chủ (${response.status}).`,
          code: String(response.status),
        },
      };
    }

    const data = await response.json();
    if (!response.ok || data?.ok === false) {
      // auth-service trả {ok:false, error:{message, field?, details?}}; Kong trả {message}.
      const message =
        (typeof data?.error?.message === "string" && data.error.message) ||
        (typeof data?.message === "string" && data.message) ||
        "Yêu cầu đến máy chủ thất bại.";
      return {
        ok: false,
        error: {
          message,
          code: String(response.status),
          field: data?.error?.field,
          details: data?.error?.details,
        },
      };
    }
    return { ok: true, data: data.data !== undefined ? data.data : data };
  } catch (error: any) {
    return { ok: false, error: { message: error?.message || "Không thể kết nối đến máy chủ." } };
  }
}
