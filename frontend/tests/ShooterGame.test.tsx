import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../src/components/flashcards/games/sfx", () => ({ playSfx: vi.fn(), isMuted: () => false, setMuted: vi.fn() }));

import { ShooterGame } from "../src/components/flashcards/games/ShooterGame";
import type { GameCard } from "../src/components/flashcards/games/gameLogic";

const card = (n: number): GameCard => ({
  id: `c${n}`, term: `word${n}`, definition: `nghĩa ${n}`, lang_code: "en", is_due: true,
  choices: [`nghĩa ${n}`, `nhiễu ${n}a`, `nhiễu ${n}b`, `nhiễu ${n}c`]
});
const cards = (n: number) => Array.from({ length: n }, (_, i) => card(i + 1));

const FAKE = ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "performance", "Date"] as const;

function setup(opts: { mode?: "relax" | "challenge"; n?: number } = {}) {
  const onFinish = vi.fn();
  const onPlayAudio = vi.fn();
  render(<ShooterGame cards={cards(opts.n ?? 5)} mode={opts.mode ?? "relax"} onPlayAudio={onPlayAudio} onFinish={onFinish} />);
  return { onFinish, onPlayAudio };
}

const advance = async (ms: number) => { await act(async () => { vi.advanceTimersByTime(ms); }); };
const currentId = () => `c${screen.getByTestId("shooter-word").textContent!.replace("word", "")}`;
const bubble = (id: string) => screen.getByTestId(`shooter-bubble-${id}`);
const enableAssist = () => {
  const btn = screen.getByRole("button", { name: /Ngắm hỗ trợ/ });
  if (btn.getAttribute("aria-pressed") !== "true") fireEvent.click(btn);
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: [...FAKE] });
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
});

describe("ShooterGame", () => {
  it("hiện từ trên súng, các bóng nghĩa (gồm bóng đúng) và HUD; Thư giãn không có mạng", async () => {
    setup();
    await advance(50);
    expect(screen.getByTestId("shooter-word")).toHaveTextContent(/^word\d$/);
    const id = currentId();
    expect(bubble(id)).toHaveAttribute("aria-label", `nghĩa ${id.slice(1)}`);
    expect(screen.getAllByTestId(/^shooter-bubble-/).length).toBeGreaterThanOrEqual(4);
    expect(screen.getByTestId("shooter-score")).toHaveTextContent("Điểm: 0");
    expect(screen.getByTestId("shooter-progress")).toHaveTextContent("Từ 1/5");
    expect(screen.queryByTestId("shooter-lives")).not.toBeInTheDocument();
  });

  it("Thử thách hiện 3 mạng", async () => {
    setup({ mode: "challenge" });
    await advance(50);
    expect(screen.getByTestId("shooter-lives")).toHaveAttribute("aria-label", "Còn 3 mạng");
  });

  it("ngắm hỗ trợ: chạm bóng đúng -> trúng, +10 điểm, combo 1, phát âm từ, sang từ kế", async () => {
    const { onPlayAudio } = setup();
    await advance(50);
    enableAssist();
    const first = currentId();
    fireEvent.click(bubble(first));
    expect(screen.getByTestId("shooter-bullet")).toBeInTheDocument();
    await advance(1200);
    expect(screen.getByTestId("shooter-score")).toHaveTextContent("Điểm: 10");
    expect(screen.getByTestId("shooter-combo")).toHaveTextContent("Combo 1");
    expect(onPlayAudio).toHaveBeenCalledWith(undefined, `word${first.slice(1)}`, "en", undefined);
    expect(screen.getByTestId("shooter-progress")).toHaveTextContent("Từ 2/5");
    expect(currentId()).not.toBe(first);
  });

  it("bắn đúng chỉ sinh thêm MỘT bóng mới; các bóng khác giữ nguyên, sân không bị làm lại", async () => {
    setup({ n: 10 });
    await advance(50);
    enableAssist();
    const idsBefore = screen.getAllByTestId(/^shooter-bubble-/).map((b) => b.getAttribute("data-bubble-id")!);
    const positions = new Map(idsBefore.map((id) => [id, bubble(id).style.left]));
    const target = currentId();
    fireEvent.click(bubble(target));
    await advance(1500);
    const idsAfter = screen.getAllByTestId(/^shooter-bubble-/).map((b) => b.getAttribute("data-bubble-id")!);
    const added = idsAfter.filter((id) => !idsBefore.includes(id));
    const removed = idsBefore.filter((id) => !idsAfter.includes(id));
    expect(added).toHaveLength(1);
    expect(removed).toEqual([target]);
    expect(idsAfter).toHaveLength(idsBefore.length);
    for (const id of idsBefore.filter((x) => x !== target)) {
      // cùng cột (chỉ lắc nhẹ sang hai bên), không bị sinh lại ở vị trí khác
      expect(Math.abs(parseFloat(bubble(id).style.left) - parseFloat(positions.get(id)!))).toBeLessThan(3);
    }
    // nghĩa của bóng mới nằm trong danh sách từ đã lưu
    expect(bubble(added[0]).getAttribute("aria-label")).toMatch(/^nghĩa \d+$/);
  });

  it("bắn sai: mất combo, không mất mạng, không sang từ kế", async () => {
    setup({ mode: "challenge" });
    await advance(50);
    enableAssist();
    const answer = currentId();
    const wrong = screen.getAllByTestId(/^shooter-bubble-/).find((b) => b.getAttribute("data-bubble-id") !== answer)!;
    fireEvent.click(wrong);
    await advance(1200);
    expect(screen.getByTestId("shooter-score")).toHaveTextContent("Điểm: 0");
    expect(screen.getByTestId("shooter-lives")).toHaveAttribute("aria-label", "Còn 3 mạng");
    expect(screen.getByTestId("shooter-progress")).toHaveTextContent("Từ 1/5");
    expect(currentId()).toBe(answer);
  });

  it("bàn phím: ←/→ chọn bóng, Enter bắn; phím số bắn nhanh", async () => {
    setup();
    await advance(50);
    fireEvent.keyDown(window, { key: "ArrowRight" });
    fireEvent.keyDown(window, { key: "Enter" });
    expect(screen.getByTestId("shooter-bullet")).toBeInTheDocument();
    await advance(2500); // đạn bay xong
    fireEvent.keyDown(window, { key: "1" });
    expect(screen.getByTestId("shooter-bullet")).toBeInTheDocument();
  });

  it("tạm dừng bằng phím P: bóng đứng yên; bấm lại để tiếp tục", async () => {
    setup();
    await advance(50);
    const id = currentId();
    fireEvent.keyDown(window, { key: "p" });
    expect(screen.getByTestId("shooter-paused")).toBeInTheDocument();
    const top = bubble(id).style.top;
    await advance(3000);
    expect(bubble(id).style.top).toBe(top);
    fireEvent.click(screen.getByTestId("shooter-paused"));
    await advance(1000);
    expect(screen.queryByTestId("shooter-paused")).not.toBeInTheDocument();
    expect(bubble(id).style.top).not.toBe(top);
  });

  it("chuyển sang tab khác thì tự tạm dừng", async () => {
    setup();
    await advance(50);
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    act(() => { document.dispatchEvent(new Event("visibilitychange")); });
    expect(screen.getByTestId("shooter-paused")).toBeInTheDocument();
  });

  it("bắn đúng hết các từ -> onFinish với kết quả từng từ", async () => {
    const { onFinish } = setup({ n: 5 });
    await advance(50);
    enableAssist();
    for (let i = 0; i < 5; i++) {
      fireEvent.click(bubble(currentId()));
      await advance(1500);
    }
    await advance(500);
    expect(onFinish).toHaveBeenCalledTimes(1);
    const [items] = onFinish.mock.calls[0];
    expect(items).toHaveLength(5);
    expect(items.every((x: any) => x.correct && x.attempts === 0)).toBe(true);
    expect(new Set(items.map((x: any) => x.card_id)).size).toBe(5);
  });

  it("Thử thách: không bắn thì bóng đúng trôi mất, hết 3 mạng thì kết thúc với 3 kết quả chưa nhớ", async () => {
    const { onFinish } = setup({ mode: "challenge", n: 8 });
    await advance(90_000);
    expect(onFinish).toHaveBeenCalledTimes(1);
    const [items] = onFinish.mock.calls[0];
    expect(items).toHaveLength(3);
    expect(items.every((x: any) => !x.correct)).toBe(true);
  });

  it("giảm chuyển động: bóng đứng yên, không mất mạng, có ghi chú", async () => {
    vi.stubGlobal("matchMedia", (q: string) => ({ matches: q.includes("reduce"), media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
    setup({ mode: "challenge" });
    await advance(50);
    expect(screen.queryByTestId("shooter-lives")).not.toBeInTheDocument();
    const id = currentId();
    const top = bubble(id).style.top;
    await advance(30_000);
    expect(bubble(id).style.top).toBe(top);
    expect(screen.getByText(/giảm chuyển động/i)).toBeInTheDocument();
  });

  it("bấm nút nghe phát âm từ trên súng mà không bắn", async () => {
    const { onPlayAudio } = setup();
    await advance(50);
    fireEvent.click(screen.getByRole("button", { name: "Nghe phát âm" }));
    expect(onPlayAudio).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("shooter-bullet")).not.toBeInTheDocument();
  });
});
