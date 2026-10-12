import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getApiUrl,
  getToken,
  getTokenExpiry,
  installAuthFetchInterceptor,
  isTokenRemembered,
  removeToken,
  request,
  setToken,
  setUnauthorizedHandler,
} from "../src/services/apiClient";

function fakeJwt(payload: object): string {
  const b64 = (o: object) => btoa(JSON.stringify(o)).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `${b64({ alg: "HS256" })}.${b64(payload)}.sig`;
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
});
afterEach(() => {
  vi.restoreAllMocks();
  setUnauthorizedHandler(null);
});

describe("lưu token", () => {
  it("mặc định chỉ lưu trong sessionStorage", () => {
    setToken("abc");
    expect(sessionStorage.getItem("iuh_portal_ai_token")).toBe("abc");
    expect(localStorage.getItem("iuh_portal_ai_token")).toBeNull();
    expect(getToken()).toBe("abc");
    expect(isTokenRemembered()).toBe(false);
  });

  it("ghi nhớ đăng nhập => localStorage, và không để token ở cả hai nơi", () => {
    setToken("old", false);
    setToken("new", true);
    expect(localStorage.getItem("iuh_portal_ai_token")).toBe("new");
    expect(sessionStorage.getItem("iuh_portal_ai_token")).toBeNull();
    expect(isTokenRemembered()).toBe(true);
  });

  it("setToken không đổi kiểu lưu khi làm mới token (tham số remember mặc định)", () => {
    setToken("a", true);
    setToken("b");
    expect(localStorage.getItem("iuh_portal_ai_token")).toBe("b");
  });

  it("removeToken xóa ở cả hai nơi", () => {
    setToken("a", true);
    removeToken();
    expect(getToken()).toBeNull();
  });

  it("đọc hạn dùng từ claim exp, null nếu token hỏng", () => {
    expect(getTokenExpiry(fakeJwt({ exp: 1_900_000_000 }))).toBe(1_900_000_000_000);
    expect(getTokenExpiry("not-a-jwt")).toBeNull();
    expect(getTokenExpiry(null)).toBeNull();
  });
});

describe("getApiUrl", () => {
  it("giữ nguyên đường dẫn khi không có base", () => {
    expect(getApiUrl("/api/auth/me")).toBe("/api/auth/me");
  });
});

describe("request()", () => {
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

  it("gắn Authorization khi có token và bóc lớp data", async () => {
    setToken("tok");
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ ok: true, data: { id: 1 } }));
    const res = await request<{ id: number }>("/api/auth/me");
    expect(res).toEqual({ ok: true, data: { id: 1 } });
    const headers = spy.mock.calls[0][1]!.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok");
  });

  it("chuyển lỗi chuẩn của auth-service kèm field và details", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      json({ ok: false, error: { message: "Sai", field: "email", details: [{ field: "email", message: "Sai" }] } }, 400)
    );
    const res = await request("/api/auth/register", { method: "POST" });
    expect(res).toMatchObject({ ok: false, error: { message: "Sai", code: "400", field: "email" } });
  });

  it("hiểu lỗi dạng {message} của Kong", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ message: "Unauthorized" }, 401));
    const res = await request("/api/auth/me");
    expect(res).toMatchObject({ ok: false, error: { message: "Unauthorized", code: "401" } });
  });

  it("không ném lỗi khi mạng hỏng", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Failed to fetch"));
    expect(await request("/api/auth/me")).toMatchObject({ ok: false, error: { message: "Failed to fetch" } });
  });
});

describe("interceptor 401", () => {
  it("gọi handler khi API trả 401 cho yêu cầu mang token hiện tại, nhưng bỏ qua form đăng nhập/đổi mật khẩu", async () => {
    const original = vi.fn(async () => new Response("{}", { status: 401 }));
    window.fetch = original as unknown as typeof fetch;
    installAuthFetchInterceptor();

    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    setToken("tok");
    const auth = { headers: { Authorization: "Bearer tok" } };

    await window.fetch("/api/v1/chat/sessions", auth);
    expect(handler).toHaveBeenCalledTimes(1);

    await window.fetch("/api/auth/login", auth);
    await window.fetch("/api/auth/change-password", auth);
    expect(handler).toHaveBeenCalledTimes(1);

    await window.fetch("/api/v1/chat/sessions", { headers: { Authorization: "Bearer other" } });
    await window.fetch("/api/v1/chat/sessions");
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
