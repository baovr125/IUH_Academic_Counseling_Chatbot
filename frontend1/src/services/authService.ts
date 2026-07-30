import type { ApiResult, AuthResponse, LoginPayload, RegisterPayload } from "../types";
import { MOCK_USER } from "../mock/mockData";
import { delay } from "./utils";

// ----------------------------------------------------------------------------
// CONTRACT: keep this function signature identical when swapping to the real
// backend. Real implementation will just replace the body with:
//   const res = await fetch(`${API_BASE}/auth/login`, { method: "POST", body: ... })
//   return res.json();
// ----------------------------------------------------------------------------

export async function login(payload: LoginPayload): Promise<ApiResult<AuthResponse>> {
  await delay(1200);

  if (!payload.identifier || !payload.password) {
    return { ok: false, error: { message: "Vui lòng nhập đầy đủ thông tin đăng nhập." } };
  }

  return {
    ok: true,
    data: {
      user: MOCK_USER,
      token: "mock_jwt_token_" + Date.now(),
    },
  };
}

export async function register(payload: RegisterPayload): Promise<ApiResult<AuthResponse>> {
  await delay(1500);

  if (payload.password !== payload.confirmPassword) {
    return { ok: false, error: { message: "Mật khẩu xác nhận không khớp." } };
  }

  return {
    ok: true,
    data: {
      user: { ...MOCK_USER, fullName: payload.fullName, email: payload.identifier },
      token: "mock_jwt_token_" + Date.now(),
    },
  };
}

export async function logout(): Promise<ApiResult<null>> {
  await delay(300);
  return { ok: true, data: null };
}

export async function fetchCurrentUser(): Promise<ApiResult<AuthResponse["user"]>> {
  await delay(500);
  return { ok: true, data: MOCK_USER };
}
