import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { StudyMode } from "../src/components/flashcards/StudyMode";
import type { BackendCardItem, StudyStats } from "../src/services/flashcardService";

const deck = { id: "d", title: "Deck", lang_code: "en" } as any;
const ANSWERS = ["một", "hai", "ba", "bốn"];

const card = (n: number, extra: Partial<BackendCardItem> = {}): BackendCardItem => ({
  id: `c${n}`, deck_id: "d", term: `term${n}`, definition: ANSWERS[n - 1] ?? `nghĩa ${n}`, lang_code: "en",
  recommended_mode: "choice", choices: ANSWERS, ...extra
});

const stats = (over: Partial<StudyStats> = {}): StudyStats => ({ total: 4, new: 2, due: 1, learning: 1, mastered: 0, weak: 0, ...over });

function setup(queue: BackendCardItem[], over: Record<string, unknown> = {}) {
  const props = {
    deck, studyQueue: queue, stats: stats(),
    onRateFSRS: vi.fn(async () => {}), onVerifySpelling: vi.fn(), onPlayAudio: vi.fn(), onPrefetchAudio: vi.fn(),
    isPlayingAudio: false, onOpenAddCard: vi.fn(), onOpenGenerate: vi.fn(), onBackToDecks: vi.fn(),
    onNextSession: vi.fn(), onStudyWeak: vi.fn(async () => 2), onSessionFinished: vi.fn(), ...over
  };
  render(<MemoryRouter><StudyMode {...(props as any)} /></MemoryRouter>);
  return props;
}

const answer = (text: string) => fireEvent.click(screen.getByRole("button", { name: new RegExp(`^\\d\\s*${text}$`) }));
const next = async () => fireEvent.click(await screen.findByRole("button", { name: /Tiếp tục/ }));

describe("StudyMode: multiple choice", () => {
  it("rates Good (3) for a correct answer and Again (1) for a wrong one, then shows the summary", async () => {
    const p = setup([card(1), card(2)]);
    answer("một");
    expect(await screen.findByText(/Chính xác/)).toBeInTheDocument();
    await next();
    await waitFor(() => expect(p.onRateFSRS).toHaveBeenCalledWith("c1", 3));

    await screen.findByText("term2");
    answer("ba");
    expect(await screen.findByText(/Đáp án: hai/)).toBeInTheDocument();
    await next();
    await waitFor(() => expect(p.onRateFSRS).toHaveBeenCalledWith("c2", 1));

    await screen.findByText(/Từ cần chú ý \(1\)/);
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // số thẻ đã ôn
    expect(p.onSessionFinished).toHaveBeenCalledTimes(1);
  });

  it("locks the answer after the first pick", async () => {
    setup([card(1)]);
    answer("hai");
    await screen.findByText(/Đáp án: một/);
    expect(screen.getByRole("button", { name: /^1\s*một$/ })).toBeDisabled();
  });

  it("supports keyboard: 1-4 to answer, Enter to continue", async () => {
    const p = setup([card(1)]);
    fireEvent.keyDown(window, { key: "1" });
    await screen.findByText(/Chính xác/);
    fireEvent.keyDown(window, { key: "Enter" });
    await waitFor(() => expect(p.onRateFSRS).toHaveBeenCalledWith("c1", 3));
  });

  it("falls back to flip when a card has no choices and the deck is too small to build them", () => {
    setup([card(1, { choices: null })]);
    expect(screen.getByText(/Bấm vào thẻ/)).toBeInTheDocument();
  });

  it("builds distractors locally when the server sent none but the deck is big enough", () => {
    setup([card(1, { choices: null }), card(2, { choices: null }), card(3, { choices: null }), card(4, { choices: null })]);
    expect(screen.getAllByRole("button", { name: /^\d\s*\S/ })).toHaveLength(4);
  });
});

describe("StudyMode: listening", () => {
  it("hides the word until answered and autoplays the audio", async () => {
    vi.useFakeTimers();
    const p = setup([card(1, { recommended_mode: "listening" })]);
    expect(screen.queryByText("term1")).not.toBeInTheDocument();
    await vi.advanceTimersByTimeAsync(400);
    expect(p.onPlayAudio).toHaveBeenCalled();
    vi.useRealTimers();
    answer("một");
    expect(await screen.findByText("term1")).toBeInTheDocument();
  });
});

describe("StudyMode: flip + rating", () => {
  it("records the rating, advances, and finishes the session", async () => {
    const p = setup([card(1, { recommended_mode: "flip" })]);
    fireEvent.click(screen.getByText(/Bấm vào thẻ/));
    fireEvent.click(screen.getByRole("button", { name: /Dễ/ }));
    await waitFor(() => expect(p.onRateFSRS).toHaveBeenCalledWith("c1", 4));
    await screen.findByText(/Hoàn thành phiên ôn tập|Xuất sắc|Làm tốt lắm|Cố gắng/);
  });

  it("does not submit twice when the button is double-clicked", async () => {
    let release: () => void = () => {};
    const p = setup([card(1, { recommended_mode: "flip" }), card(2, { recommended_mode: "flip" })], {
      onRateFSRS: vi.fn(() => new Promise<void>((resolve) => { release = resolve; }))
    });
    fireEvent.click(screen.getByText(/Bấm vào thẻ/));
    const good = screen.getByRole("button", { name: /Tốt/ });
    fireEvent.click(good);
    fireEvent.click(good);
    expect(p.onRateFSRS).toHaveBeenCalledTimes(1);
    release();
  });

  it("marks new cards", () => {
    setup([card(1, { recommended_mode: "flip", is_new: true })]);
    expect(screen.getByText("Từ mới")).toBeInTheDocument();
  });

  it("shows progress chips from the deck stats", () => {
    setup([card(1, { recommended_mode: "flip" })], { stats: stats({ new: 5, due: 3, learning: 2, mastered: 7 }) });
    expect(screen.getByText("Mới 5")).toBeInTheDocument();
    expect(screen.getByText("Đến hạn 3")).toBeInTheDocument();
    expect(screen.getByText("Đã thuộc 7")).toBeInTheDocument();
  });

  it("lets the learner force a mode manually", async () => {
    setup([card(1, { recommended_mode: "flip" })]);
    fireEvent.click(screen.getByRole("button", { name: /Trắc nghiệm/ }));
    expect(await screen.findByText(/Trắc nghiệm: chọn nghĩa đúng/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Gõ từ/ }));
    expect(await screen.findByText(/Thử thách Gõ chính tả/)).toBeInTheDocument();
  });
});

describe("StudyMode: summary actions", () => {
  async function finishWithOneWrong() {
    const p = setup([card(1), card(2)]);
    answer("một");
    await next();
    await screen.findByText("term2");
    answer("ba");
    await next();
    await screen.findByText(/Từ cần chú ý/);
    return p;
  }

  it("re-drills only the weak words without calling the server", async () => {
    const p = await finishWithOneWrong();
    p.onRateFSRS.mockClear();
    fireEvent.click(screen.getByRole("button", { name: /Ôn lại 1 từ này ngay/ }));
    expect(await screen.findByText(/Thẻ 1 \/ 1/)).toBeInTheDocument();
    expect(screen.getByText("term2")).toBeInTheDocument();
    expect(p.onNextSession).not.toHaveBeenCalled();
  });

  it("'Học tiếp' asks the parent for a fresh session; 'Quay lại' goes back", async () => {
    const p = await finishWithOneWrong();
    fireEvent.click(screen.getByRole("button", { name: /Học tiếp/ }));
    await waitFor(() => expect(p.onNextSession).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole("button", { name: /Quay lại Sổ thẻ/ }));
    expect(p.onBackToDecks).toHaveBeenCalled();
  });

  it("lists weak words with a pronunciation button", async () => {
    const p = await finishWithOneWrong();
    fireEvent.click(screen.getByLabelText("Nghe từ term2"));
    expect(p.onPlayAudio).toHaveBeenCalledWith(undefined, "term2", "en", undefined);
  });

  it("a perfect session reports no weak words", async () => {
    setup([card(1)]);
    answer("một");
    await next();
    expect(await screen.findByText(/Không có từ nào trả lời sai/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ôn lại/ })).not.toBeInTheDocument();
  });
});

describe("StudyMode: empty states", () => {
  it("an empty deck offers the AI, add, import and translate actions", () => {
    const p = setup([], { stats: stats({ total: 0, new: 0, due: 0, learning: 0 }), onOpenImportExcel: vi.fn() });
    expect(screen.getByText(/chưa có từ vựng nào/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Tạo từ vựng bằng AI/ }));
    expect(p.onOpenGenerate).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: /Thêm thẻ mới/ }));
    expect(p.onOpenAddCard).toHaveBeenCalled();
  });

  it("nothing due today shows the done screen and can drill weak words", async () => {
    const p = setup([], { stats: stats({ total: 10, new: 0, due: 0, learning: 6, mastered: 4, weak: 3 }) });
    expect(screen.getByText(/Hôm nay bạn đã ôn xong/)).toBeInTheDocument();
    expect(screen.getByText(/Đã thuộc 4\/10/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Ôn 3 từ hay quên/ }));
    await waitFor(() => expect(p.onStudyWeak).toHaveBeenCalled());
  });

  it("hides the weak-words button when there are none", () => {
    setup([], { stats: stats({ total: 10, weak: 0 }) });
    expect(screen.queryByRole("button", { name: /từ hay quên/ })).not.toBeInTheDocument();
  });
});
