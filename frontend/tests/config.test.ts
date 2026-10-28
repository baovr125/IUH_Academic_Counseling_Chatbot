import { afterEach, describe, expect, it, vi } from "vitest";
import { getApiBaseUrl, isDocTranslationEnabled, normalizeApiBase } from "../src/config";

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

describe("isDocTranslationEnabled", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("mặc định bật khi chưa đặt biến", () => {
    vi.stubEnv("VITE_FEATURE_DOC_TRANSLATION", "");
    expect(isDocTranslationEnabled()).toBe(true);
  });

  it.each(["false", "FALSE", " 0 "])("tắt khi đặt %j", (value) => {
    vi.stubEnv("VITE_FEATURE_DOC_TRANSLATION", value);
    expect(isDocTranslationEnabled()).toBe(false);
  });

  it.each(["true", "1"])("vẫn bật khi đặt %j", (value) => {
    vi.stubEnv("VITE_FEATURE_DOC_TRANSLATION", value);
    expect(isDocTranslationEnabled()).toBe(true);
  });
});
