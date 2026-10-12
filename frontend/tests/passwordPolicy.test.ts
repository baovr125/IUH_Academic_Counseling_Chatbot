import { describe, expect, it } from "vitest";
import { checkPassword, estimateStrength, validatePassword } from "../src/services/passwordPolicy";

describe("passwordPolicy (phải khớp quy tắc của auth-service)", () => {
  it.each([
    ["", "auth.err.passwordRequired"],
    ["Ab1", "auth.err.passwordShort"],
    ["abcdefgh", "auth.err.passwordDigit"],
    ["12345678", "auth.err.passwordLetter"],
    ["a1" + "x".repeat(80), "auth.err.passwordLong"],
  ])("từ chối %j", (pw, key) => {
    expect(validatePassword(pw)).toBe(key);
  });

  it("chấp nhận mật khẩu hợp lệ", () => {
    expect(validatePassword("Tr0ub4dor-Horse")).toBeNull();
  });

  it("đếm theo byte UTF-8 như bcrypt (ký tự có dấu chiếm 2-3 byte)", () => {
    const vn = "ắ1" + "ẩ".repeat(30); // ~ 92 byte
    expect(checkPassword(vn).bytes).toBe(false);
    expect(validatePassword(vn)).toBe("auth.err.passwordLong");
  });

  it("từ chối mật khẩu trùng phần local của email", () => {
    expect(validatePassword("20012345a", "20012345a@student.iuh.edu.vn")).toBe("auth.err.passwordEqualsEmail");
  });

  it("ước lượng độ mạnh chỉ phân loại khi đã đạt quy tắc bắt buộc", () => {
    expect(estimateStrength("abc")).toBe("weak");
    expect(estimateStrength("abcdefg1")).toBe("medium");
    expect(estimateStrength("Correct-Horse-Battery-9")).toBe("strong");
  });
});
