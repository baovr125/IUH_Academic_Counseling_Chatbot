import React from "react";
import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../src/components/flashcards/games/sfx", () => ({ playSfx: vi.fn(), isMuted: () => false, setMuted: vi.fn() }));

import { ShooterGame } from "../src/components/flashcards/games/ShooterGame";
import type { GameCard } from "../src/components/flashcards/games/gameLogic";

/**
 * Quy ước "khối khóa theme": phần tử có data-theme-lock="light|dark" luôn giữ một màu nền ở CẢ HAI chế độ,
 * nên KHÔNG phần tử nào trong khối (kể cả chính nó) được có lớp `dark:`. Nếu có, chữ/nút sẽ đổi màu trong khi
 * nền không đổi (từng làm từ trên súng Bắn bóng chỉ còn 1,01:1 ở chế độ tối).
 */
export function darkVariantsInsideLocks(root: ParentNode): string[] {
  const bad: string[] = [];
  root.querySelectorAll("[data-theme-lock]").forEach((lock) => {
    const all = [lock, ...Array.from(lock.querySelectorAll("*"))];
    for (const el of all) {
      const cls = (el.getAttribute("class") ?? "").split(/\s+/).filter((c) => c.includes("dark:"));
      if (cls.length) bad.push(`${(lock as HTMLElement).dataset.themeLock}: <${el.tagName.toLowerCase()}> ${cls.join(" ")}`);
    }
  });
  return bad;
}

const FAKE = ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "performance", "Date"] as const;
const card = (n: number): GameCard => ({
  id: `c${n}`, term: `word${n}`, definition: `nghĩa ${n}`, lang_code: "en", is_due: true, phonetic: "/wɜːd/",
  choices: [`nghĩa ${n}`, `nhiễu ${n}a`, `nhiễu ${n}b`, `nhiễu ${n}c`]
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: [...FAKE] });
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
});
afterEach(() => {
  vi.useRealTimers();
});

describe("khối khóa theme", () => {
  it("bắt được lỗi khi khối khóa chứa lớp dark:", () => {
    const { container } = render(
      <div data-theme-lock="light" className="bg-white">
        <span className="text-slate-800 dark:text-slate-100">x</span>
      </div>
    );
    expect(darkVariantsInsideLocks(container)).toEqual(["light: <span> dark:text-slate-100"]);
  });

  it("Bắn bóng: đấu trường (tối) và tấm từ đang nạp (trắng) không có lớp dark:", async () => {
    const { container } = render(
      <ShooterGame cards={[1, 2, 3, 4, 5].map(card)} mode="challenge" onPlayAudio={vi.fn()} onFinish={vi.fn()} />
    );
    await act(async () => { vi.advanceTimersByTime(50); });

    const locks = Array.from(container.querySelectorAll<HTMLElement>("[data-theme-lock]")).map((e) => e.dataset.themeLock);
    expect(locks).toEqual(expect.arrayContaining(["dark", "light"]));
    expect(container.querySelector('[data-theme-lock="light"] [data-testid="shooter-word"]')).not.toBeNull();
    expect(darkVariantsInsideLocks(container)).toEqual([]);
  });
});
