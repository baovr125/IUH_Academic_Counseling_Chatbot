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
