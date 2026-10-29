import { describe, expect, it } from "vitest";

/**
 * Khóa hệ màu "trắng và xanh nhẹ" của giao diện (quét tĩnh mã nguồn, cùng cách làm với themeConsistency):
 *
 * P1  Không dùng họ màu ngoài hệ: indigo, violet, purple, fuchsia, pink, cyan, teal, lime, yellow.
 * P2  `blue-*` không dùng trực tiếp: dùng token `brand-*` (tailwind.config.js) để đổi sắc xanh ở một chỗ.
 * P3  Màu cam chỉ dành cho "tín hiệu đặc biệt" (streak, cần ôn, combo): chỉ các tệp trong ORANGE_ALLOWED được dùng.
 * P4  Không dùng gradient có amber (cặp cam-hổ phách cũ) và không dùng màu hex tùy ý cho nền/chữ/viền/gradient
 *     (ví dụ `from-[#152a6e]`): mọi màu phải đi qua token.
 *
 * Cần ngoại lệ có chủ ý? Thêm tệp vào ORANGE_ALLOWED (kèm lý do) thay vì dùng lại màu cũ ở nơi khác.
 */
const SOURCES = import.meta.glob("../src/{components,pages}/**/*.tsx", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const relOf = (key: string) => key.replace("../src/", "");

/** Tệp được phép dùng cam, kèm lý do (chỉ cho tín hiệu đặc biệt). */
const ORANGE_ALLOWED = new Set<string>([
  "components/flashcards/ui/FcBadge.tsx", // tông "orange" = cần ôn / đến hạn
  "components/flashcards/ui/FcStat.tsx", // ô số liệu cùng tông tín hiệu
  "components/dashboard/FlashcardDueCard.tsx", // số thẻ cần ôn
  "components/dashboard/LearningStreakHeatmap.tsx", // biểu tượng lửa streak
  "components/dashboard/StudentAcademicKpiCard.tsx", // huy hiệu streak
  "components/dashboard/PublicLearningProductivityCard.tsx", // huy hiệu streak
  "components/flashcards/games/ShooterGame.tsx", // combo
  "components/flashcards/games/SpeedRoundGame.tsx", // combo
]);

const UTIL = "(?:bg|text|border|border-[tblrxy]|from|to|via|ring|ring-offset|shadow|fill|stroke|divide|outline|placeholder|decoration|accent|caret)";
const FORBIDDEN = new RegExp(`(?<![\\w-])(?:[a-z-]+:)*${UTIL}-(indigo|violet|purple|fuchsia|pink|cyan|teal|lime|yellow)-\\d`, "g");
const RAW_BLUE = new RegExp(`(?<![\\w-])(?:[a-z-]+:)*${UTIL}-blue-\\d`, "g");
const ORANGE = new RegExp(`(?<![\\w-])(?:[a-z-]+:)*${UTIL}-orange-\\d`, "g");
const AMBER_GRADIENT = /(?<![\w-])(?:[a-z-]+:)*(?:from|via|to)-amber-\d/g;
const HEX_UTIL = /(?<![\w-])(?:[a-z-]+:)*(?:bg|text|border|from|via|to|ring|shadow)-\[#[0-9a-fA-F]{3,8}\]/g;

function lineOf(src: string, index: number) {
  return src.slice(0, index).split("\n").length;
}

function findAll(re: RegExp) {
  const out: string[] = [];
  for (const [key, raw] of Object.entries(SOURCES)) {
    const rel = relOf(key);
    for (const m of raw.matchAll(re)) out.push(`${rel}:${lineOf(raw, m.index ?? 0)} ${m[0]}`);
  }
  return out;
}

describe("nhất quán hệ màu (quét tĩnh)", () => {
  it("P1: không dùng họ màu ngoài hệ (indigo/violet/purple/...)", () => {
    expect(findAll(FORBIDDEN)).toEqual([]);
  });

  it("P2: dùng token brand-* thay cho blue-*", () => {
    expect(findAll(RAW_BLUE)).toEqual([]);
  });

  it("P3: cam chỉ xuất hiện ở các tệp tín hiệu đặc biệt", () => {
    const bad = findAll(ORANGE).filter((hit) => !ORANGE_ALLOWED.has(hit.split(":")[0]));
    expect(bad).toEqual([]);
  });

  it("P3b: mọi tệp trong ORANGE_ALLOWED vẫn còn dùng cam (danh sách không thừa)", () => {
    const used = new Set(findAll(ORANGE).map((hit) => hit.split(":")[0]));
    expect([...ORANGE_ALLOWED].filter((f) => !used.has(f))).toEqual([]);
  });

  it("P4: không gradient amber và không màu hex tùy ý trong lớp tiện ích", () => {
    expect([...findAll(AMBER_GRADIENT), ...findAll(HEX_UTIL)]).toEqual([]);
  });
});
