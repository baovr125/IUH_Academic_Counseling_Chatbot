/** Chuẩn hóa gốc URL API: undefined/null thành rỗng và bỏ dấu "/" ở cuối. */
export function normalizeApiBase(raw: unknown): string {
  return (raw === undefined || raw === null ? "" : String(raw)).replace(/\/+$/, "");
}

/**
 * Gốc URL của API (biến build VITE_API_BASE_URL).
 * Rỗng nghĩa là gọi cùng origin (nginx/Vite proxy chuyển /api sang Kong).
 */
export function getApiBaseUrl(): string {
  const env = (import.meta as any).env || {};
  return normalizeApiBase(env.VITE_API_BASE_URL);
}

/**
 * Tính năng Dịch tài liệu (doc-translation-service) có hiện trên giao diện không.
 * Mặc định bật; đặt VITE_FEATURE_DOC_TRANSLATION=false (hoặc 0) lúc build để khóa khi service không được triển khai.
 */
export function isDocTranslationEnabled(): boolean {
  const raw = String(import.meta.env.VITE_FEATURE_DOC_TRANSLATION ?? "").trim().toLowerCase();
  return raw !== "false" && raw !== "0";
}
