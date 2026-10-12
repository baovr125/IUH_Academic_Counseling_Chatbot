/**
 * Quy tắc mật khẩu phía client — phải khớp `check_password_policy` ở
 * services/auth_service/app/schemas/auth.py (server vẫn là nguồn quyết định cuối cùng).
 *
 * Hàm trả về KHÓA dịch của lỗi đầu tiên (hoặc null nếu hợp lệ) để UI tự dịch theo ngôn ngữ.
 */
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_BYTES = 72;

export type PasswordStrength = "weak" | "medium" | "strong";

export interface PasswordChecks {
  length: boolean;
  letter: boolean;
  digit: boolean;
  bytes: boolean;
}

export function checkPassword(password: string): PasswordChecks {
  return {
    length: password.length >= PASSWORD_MIN_LENGTH,
    letter: /[A-Za-z]/.test(password),
    digit: /\d/.test(password),
    bytes: new TextEncoder().encode(password).length <= PASSWORD_MAX_BYTES,
  };
}

export function validatePassword(password: string, email?: string): string | null {
  if (!password) return "auth.err.passwordRequired";
  const c = checkPassword(password);
  if (!c.length) return "auth.err.passwordShort";
  if (!c.bytes) return "auth.err.passwordLong";
  if (!c.letter) return "auth.err.passwordLetter";
  if (!c.digit) return "auth.err.passwordDigit";
  if (email) {
    const local = email.split("@")[0]?.toLowerCase();
    if (local && (password.toLowerCase() === local || password.toLowerCase() === email.toLowerCase())) {
      return "auth.err.passwordEqualsEmail";
    }
  }
  return null;
}

/** Độ mạnh chỉ mang tính gợi ý (không thay thế quy tắc bắt buộc ở trên). */
export function estimateStrength(password: string): PasswordStrength {
  const c = checkPassword(password);
  if (!(c.length && c.letter && c.digit && c.bytes)) return "weak";
  let score = 0;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score >= 2 ? "strong" : "medium";
}
