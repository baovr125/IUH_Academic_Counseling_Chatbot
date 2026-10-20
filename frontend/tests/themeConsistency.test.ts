import { describe, expect, it } from "vitest";

/**
 * Quét tĩnh mã nguồn để chặn các lỗi Dark Mode đã gặp. Quét theo từng chuỗi ký tự ("..." '...' `...`)
 * có chứa lớp Tailwind, nên chỉ bắt được lỗi nằm trong CÙNG một chuỗi lớp (đúng cách mã hiện viết).
 *
 * R1  hover:bg-* + dark:bg-* mà thiếu dark:hover:bg-*: `dark:` đứng sau `hover:` trong CSS nên thắng khi rê chuột,
 *     làm mất phản hồi hover ở chế độ tối.
 * R2  Nền sáng đặc (bg-white, bg-slate-50, bg-slate-100) không có dark:bg-* trong cùng chuỗi: chói/chữ kế thừa
 *     `dark:text-slate-100` của MainLayout sẽ trắng trên trắng.
 *
 * LEGACY_UNCONVERTED là danh sách các tệp CHƯA có dark mode được tạm miễn kiểm tra (hiện RỖNG: Đợt 3 đã phủ hết).
 * Tệp nào có lớp `dark:` mà vẫn nằm trong danh sách sẽ bị báo lỗi (cơ chế "ratchet"), để danh sách chỉ ngắn dần.
 * Cần ngoại lệ có chủ ý? Thêm vào ALLOW kèm lý do, hoặc bọc khối bằng data-theme-lock (xem themeLock.test.tsx).
 */
// Đọc mã nguồn dạng chuỗi qua Vite (dự án không cài @types/node nên không dùng node:fs).
const SOURCES = import.meta.glob("../src/{components,pages}/**/*.tsx", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const relOf = (key: string) => key.replace("../src/", "");

const LEGACY_UNCONVERTED = new Set<string>([]);

/** "đường dẫn:token" được phép vi phạm R2, kèm lý do. */
const ALLOW = new Set<string>([
  // Ô logo luôn trắng để logo xanh đậm không chìm vào nền thanh bên / banner navy (có chú thích tại chỗ).
  "components/layout/Sidebar.tsx:bg-white",
  "pages/LoginPage.tsx:bg-white",
  // Núm gạt của công tắc luôn trắng trên nền xanh/xám của công tắc.
  "pages/SettingsPage.tsx:bg-white"
]);

const STRING = /"([^"\n]*)"|'([^'\n]*)'|`([^`]*)`/g;

interface Hit {
  file: string;
  line: number;
  rule: "R1" | "R2";
  detail: string;
}

function scan(rel: string, raw: string): Hit[] {
  // Nối các chuỗi viết bằng "a " + "b " thành một chuỗi (giữ nguyên số dòng) vì chúng là một danh sách lớp.
  const src = raw.replace(/(["'`])\s*\+\s*(["'`])/g, (m) => " " + "\n".repeat(m.split("\n").length - 1));
  const hits: Hit[] = [];
  for (const m of src.matchAll(STRING)) {
    const text = m[1] ?? m[2] ?? m[3] ?? "";
    const tokens = text.split(/\s+/).filter(Boolean);
    if (tokens.length < 2) continue;
    const line = src.slice(0, m.index).split("\n").length;

    const hasDarkBg = tokens.some((t) => /^dark:bg-/.test(t));
    const hasDarkHoverBg = tokens.some((t) => /^dark:hover:bg-/.test(t));
    const hoverBg = tokens.find((t) => /^hover:bg-/.test(t));
    if (hoverBg && hasDarkBg && !hasDarkHoverBg) {
      hits.push({ file: rel, line, rule: "R1", detail: hoverBg });
    }

    const surface = tokens.find((t) => /^bg-(white|slate-50|slate-100)$/.test(t));
    if (surface && !hasDarkBg && !ALLOW.has(`${rel}:${surface}`)) {
      hits.push({ file: rel, line, rule: "R2", detail: surface });
    }
  }
  return hits;
}

const BY_FILE = new Map(Object.entries(SOURCES).map(([key, raw]) => [relOf(key), scan(relOf(key), raw)]));
const RAW_BY_FILE = new Map(Object.entries(SOURCES).map(([key, raw]) => [relOf(key), raw]));

const fmt = (hits: Hit[]) => hits.map((h) => `${h.file}:${h.line} [${h.rule}] ${h.detail}`);

describe("nhất quán Dark Mode (quét tĩnh)", () => {
  it("các tệp đã hỗ trợ dark mode không còn vi phạm R1/R2", () => {
    const bad = [...BY_FILE.entries()].filter(([f]) => !LEGACY_UNCONVERTED.has(f)).flatMap(([, h]) => h);
    expect(fmt(bad)).toEqual([]);
  });

  it("LEGACY_UNCONVERTED chỉ chứa tệp còn tồn tại và vẫn chưa có lớp dark: (đã làm dark mode thì gỡ ra để khóa tiến độ)", () => {
    const stale = [...LEGACY_UNCONVERTED].filter(
      (f) => !BY_FILE.has(f) || /(^|[\s"'`])dark:/.test(RAW_BY_FILE.get(f)!)
    );
    expect(stale).toEqual([]);
  });
});
