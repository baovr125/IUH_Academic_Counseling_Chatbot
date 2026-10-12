import { describe, expect, it } from "vitest";
import {
  DEFAULT_DEBOUNCE_MS,
  DOMAIN_DEBOUNCE_MS,
  LANGUAGE_STOP_DEBOUNCE_MS,
  debounceDelayMs,
  isDomainMode,
  mergeWarnings,
} from "../src/components/translation/domainMode";
import type { TranslationWarning } from "../src/types";

const warn = (code: string, message = code, severity: TranslationWarning["severity"] = "info"): TranslationWarning => ({
  code,
  severity,
  message,
});

describe("debounce theo chế độ", () => {
  it("giữ 300 ms cho dịch thông thường", () => {
    expect(debounceDelayMs("", false)).toBe(DEFAULT_DEBOUNCE_MS);
    expect(DEFAULT_DEBOUNCE_MS).toBe(300);
  });

  it("chờ 1,5 s cho cả auto lẫn domain thủ công", () => {
    expect(DOMAIN_DEBOUNCE_MS).toBe(1500);
    expect(debounceDelayMs("auto", false)).toBe(1500);
    expect(debounceDelayMs("Luật / Pháp lý", false)).toBe(1500);
    expect(debounceDelayMs("Lĩnh vực tự nhập", false)).toBe(1500);
  });

  it("không bao giờ ngắn hơn 1,5 s khi đang ở chế độ domain, kể cả khi chờ chọn ngôn ngữ", () => {
    expect(debounceDelayMs("auto", true)).toBeGreaterThanOrEqual(DOMAIN_DEBOUNCE_MS);
    expect(debounceDelayMs("", true)).toBe(LANGUAGE_STOP_DEBOUNCE_MS);
  });

  it("isDomainMode coi chuỗi rỗng/khoảng trắng là dịch thông thường", () => {
    expect(isDomainMode("")).toBe(false);
    expect(isDomainMode("   ")).toBe(false);
    expect(isDomainMode("auto")).toBe(true);
  });
});

describe("mergeWarnings", () => {
  it("giữ nhiều cảnh báo khác mã cùng lúc", () => {
    const merged = mergeWarnings([warn("A")], [warn("B")]);
    expect(merged.map((w) => w.code)).toEqual(["A", "B"]);
  });

  it("cảnh báo mới cùng mã thay thế cảnh báo cũ, không nhân đôi", () => {
    const merged = mergeWarnings([warn("A", "cũ")], [warn("A", "mới"), warn("B")]);
    expect(merged).toHaveLength(2);
    expect(merged.find((w) => w.code === "A")?.message).toBe("mới");
  });

  it("không thay đổi mảng đầu vào", () => {
    const prev = [warn("A")];
    mergeWarnings(prev, [warn("B")]);
    expect(prev).toHaveLength(1);
  });
});
