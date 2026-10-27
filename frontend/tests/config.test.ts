import { describe, expect, it } from "vitest";
import { getApiBaseUrl, normalizeApiBase } from "../src/config";

describe("normalizeApiBase", () => {
  it("trả chuỗi rỗng khi chưa đặt giá trị", () => {
    expect(normalizeApiBase(undefined)).toBe("");
    expect(normalizeApiBase(null)).toBe("");
    expect(normalizeApiBase("")).toBe("");
  });

  it("giữ nguyên URL không có dấu / cuối", () => {
    expect(normalizeApiBase("http://localhost:8000")).toBe("http://localhost:8000");
  });

  it("bỏ mọi dấu / ở cuối", () => {
    expect(normalizeApiBase("https://api.example.test//")).toBe("https://api.example.test");
  });
});

describe("getApiBaseUrl", () => {
  it("luôn trả chuỗi không kết thúc bằng /", () => {
    expect(getApiBaseUrl().endsWith("/")).toBe(false);
  });
});
