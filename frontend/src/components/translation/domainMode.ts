import type { TranslationWarning } from "../../types";

/**
 * Chế độ chuyên ngành (auto hoặc chọn thủ công) dịch bằng LLM nên chỉ gửi request sau khi người dùng
 * ngừng gõ đủ lâu, để tránh vượt giới hạn request/token của nhà cung cấp LLM.
 */
export const DOMAIN_DEBOUNCE_MS = 1500;
export const DEFAULT_DEBOUNCE_MS = 300;
/** Khi đang chờ người dùng chọn ngôn ngữ nguồn thì giãn nhịp hơn nữa (giữ hành vi cũ). */
export const LANGUAGE_STOP_DEBOUNCE_MS = 700;

/** `domain` rỗng nghĩa là "Dịch thông thường (Mặc định)" (NLLB); mọi giá trị khác là chế độ chuyên ngành. */
export function isDomainMode(domain: string): boolean {
  return Boolean(domain && domain.trim());
}

export function debounceDelayMs(domain: string, languageStopActive: boolean): number {
  if (isDomainMode(domain)) return Math.max(DOMAIN_DEBOUNCE_MS, languageStopActive ? LANGUAGE_STOP_DEBOUNCE_MS : 0);
  return languageStopActive ? LANGUAGE_STOP_DEBOUNCE_MS : DEFAULT_DEBOUNCE_MS;
}

/** Gộp cảnh báo theo `code`: cảnh báo mới cùng mã thay thế cảnh báo cũ, mã khác được giữ lại. */
export function mergeWarnings(prev: TranslationWarning[], incoming: TranslationWarning[]): TranslationWarning[] {
  const byCode = new Map<string, TranslationWarning>();
  for (const w of prev) byCode.set(w.code, w);
  for (const w of incoming) byCode.set(w.code, w);
  return Array.from(byCode.values());
}
