import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const svc = vi.hoisted(() => ({ fetchGameCards: vi.fn(), fetchGameStats: vi.fn(), submitGameSession: vi.fn() }));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "u1" } }) }));
vi.mock("../src/components/flashcards/games/sfx", () => ({ playSfx: vi.fn(), isMuted: () => false, setMuted: vi.fn() }));

import { GamesHub } from "../src/components/flashcards/games/GamesHub";

const deckOf = (lang = "en") => ({ id: "deck-1", title: "Sổ thử", lang_code: lang } as any);

const gcard = (n: number, term = `word${n}`, lang = "en") => ({
  id: `c${n}`, term, definition: `nghĩa ${n}`, lang_code: lang, is_due: true, choices: [`nghĩa ${n}`, "sai A", "sai B", "sai C"]
});
const cardsData = (game: string, cards: ReturnType<typeof gcard>[], over: Record<string, unknown> = {}) => ({
  ok: true,
  data: { game, deck_id: "deck-1", lang_code: "en", playable: true, reason: null, min_required: 4, total_cards: cards.length, due_count: cards.length, cards, ...over }
});

const emptyStats = (over: Record<string, unknown> = {}) => ({
  lang_code: "en", plays_total: 0, plays_today: 0,
  level: { level: 1, xp: 0, level_floor_xp: 0, next_level_xp: 100 },
  games: Object.fromEntries(["match", "speed", "builder", "shooter"].map((g) => [g, { plays: 0, last_played: null, best: { relax: null, challenge: null } }])),
  ...over
});

const session = (over: Record<string, unknown> = {}) => ({
  id: "s1", game: "match", mode: "relax", total: 4, correct: 4, mistakes: 0, hints: 0, best_combo: 0, duration_ms: 5000,
  score: 400, stars: 3, xp: 70, applied_review: true, reviewed_count: 3, ...over
});

function renderHub(deck = deckOf()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onPlayAudio = vi.fn();
  render(
    <QueryClientProvider client={qc}>
      <GamesHub deck={deck} onPlayAudio={onPlayAudio} />
    </QueryClientProvider>
  );
  return { onPlayAudio, qc };
}

const lastSubmit = () => svc.submitGameSession.mock.calls[svc.submitGameSession.mock.calls.length - 1][0];
const startGame = async (kind: string) => {
  await waitFor(() => expect(screen.getByTestId(`game-card-${kind}`)).toBeEnabled());
  fireEvent.click(screen.getByTestId(`game-card-${kind}`));
  await screen.findByTestId("game-stage");
};

beforeEach(() => {
  localStorage.clear();
  Object.values(svc).forEach((m) => m.mockReset());
  svc.fetchGameStats.mockResolvedValue({ ok: true, data: emptyStats() });
  svc.submitGameSession.mockResolvedValue({
    ok: true, data: { session: session(), is_record: true, previous_best: 0, idempotent_replay: false, level: { level: 1, xp: 70, level_floor_xp: 0, next_level_xp: 100 } }
  });
});
afterEach(() => vi.useRealTimers());

describe("GamesHub — màn chọn trò", () => {
  it("hiện cấp độ, 3 trò và kỷ lục theo chế độ đang chọn", async () => {
    svc.fetchGameStats.mockResolvedValue({
      ok: true,
      data: emptyStats({
        plays_today: 2,
        level: { level: 3, xp: 450, level_floor_xp: 400, next_level_xp: 900 },
        games: {
          match: { plays: 3, last_played: null, best: { relax: { score: 600, stars: 3, best_combo: 0 }, challenge: null } },
          speed: { plays: 0, last_played: null, best: { relax: null, challenge: { score: 340, stars: 2, best_combo: 9 } } },
          builder: { plays: 0, last_played: null, best: { relax: null, challenge: null } }
        }
      })
    });
    renderHub();
    expect(await screen.findByText("Cấp 3")).toBeInTheDocument();
    expect(screen.getByText("450/900 XP")).toBeInTheDocument();
    expect(screen.getByText("Hôm nay: 2 ván")).toBeInTheDocument();
    expect(screen.getAllByTestId(/^game-card-/)).toHaveLength(4);
    expect(screen.getByTestId("game-best-match")).toHaveTextContent("Kỷ lục 600");
    expect(screen.getByTestId("game-card-speed")).toHaveTextContent("Chưa có kỷ lục");

    fireEvent.click(screen.getByRole("radio", { name: /Thử thách/ }));
    expect(screen.getByTestId("game-best-speed")).toHaveTextContent("Kỷ lục 340");
    expect(screen.getByTestId("game-card-match")).toHaveTextContent("Chưa có kỷ lục");
  });

  it("Xếp chữ bị khóa với ngôn ngữ không phải chữ cái, các trò khác vẫn chơi được", async () => {
    renderHub(deckOf("ja"));
    await screen.findByText("Cấp 1");
    expect(screen.getByTestId("game-card-builder")).toBeDisabled();
    expect(screen.getByTestId("game-card-builder")).toHaveTextContent("Không hỗ trợ ngôn ngữ này");
    expect(screen.getByTestId("game-card-match")).toBeEnabled();
    expect(screen.getByTestId("game-card-speed")).toBeEnabled();
  });

  it("sổ chưa đủ thẻ: hiện lý do từ máy chủ và ở lại màn chọn", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("match", [], { playable: false, reason: "Cần ít nhất 4 thẻ có từ và nghĩa khác nhau trong sổ này để chơi (hiện có 2)." }));
    renderHub();
    fireEvent.click(await screen.findByTestId("game-card-match"));
    expect(await screen.findByTestId("games-menu-error")).toHaveTextContent("Cần ít nhất 4");
    expect(screen.queryByTestId("game-stage")).not.toBeInTheDocument();
  });

  it("lỗi tải bộ thẻ (vd chưa chạy migration) hiện thông báo", async () => {
    svc.fetchGameCards.mockResolvedValue({ ok: false, error: { code: "MIGRATION_REQUIRED", message: "Cơ sở dữ liệu chưa chạy migration 006" } });
    renderHub();
    fireEvent.click(await screen.findByTestId("game-card-speed"));
    expect(await screen.findByTestId("games-menu-error")).toHaveTextContent("migration 006");
  });

  it("lỗi tải thống kê không chặn việc chơi", async () => {
    svc.fetchGameStats.mockResolvedValue({ ok: false, error: { message: "Máy chủ bận" } });
    renderHub();
    expect(await screen.findByRole("alert")).toHaveTextContent("Máy chủ bận");
    expect(screen.getByTestId("game-card-match")).toBeEnabled();
  });

  it("ghi nhớ chế độ và công tắc 'Tính vào lịch ôn' trên trình duyệt", async () => {
    const first = renderHub();
    await screen.findByText("Cấp 1");
    fireEvent.click(screen.getByRole("radio", { name: /Thử thách/ }));
    fireEvent.click(screen.getByLabelText(/Tính vào lịch ôn/));
    first.qc.clear();
    document.body.innerHTML = "";
    renderHub();
    await screen.findByText("Cấp 1");
    expect(screen.getByRole("radio", { name: /Thử thách/ })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByLabelText(/Tính vào lịch ôn/)).not.toBeChecked();
  });
});

describe("Ghép cặp", () => {
  const four = [1, 2, 3, 4].map((n) => gcard(n));

  async function playAll(wrongFirst = false) {
    svc.fetchGameCards.mockResolvedValue(cardsData("match", four));
    renderHub();
    await startGame("match");
    if (wrongFirst) {
      fireEvent.click(screen.getByTestId("match-term-c1"));
      fireEvent.click(screen.getByTestId("match-def-c2"));
      await waitFor(() => expect(screen.getByTestId("match-progress")).toBeInTheDocument());
      await act(async () => { await new Promise((r) => setTimeout(r, 750)); }); // hết thời gian hiện lỗi
    }
    for (const n of [1, 2, 3, 4]) {
      fireEvent.click(screen.getByTestId(`match-term-c${n}`));
      fireEvent.click(screen.getByTestId(`match-def-c${n}`));
    }
  }

  it("ghép xong: gửi kết quả từng thẻ, hiện sao/điểm/kỷ lục/XP và ghi chú lịch ôn", async () => {
    await playAll();
    expect(await screen.findByTestId("game-result", {}, { timeout: 3000 })).toBeInTheDocument();
    expect(lastSubmit()).toMatchObject({ game: "match", mode: "relax", deckId: "deck-1", applyReview: true });
    expect(lastSubmit().clientRequestId).toMatch(/^fc-/);
    expect(lastSubmit().items).toHaveLength(4);
    expect(lastSubmit().items.every((i: any) => i.correct && i.attempts === 0)).toBe(true);
    expect(screen.getByTestId("game-score")).toHaveTextContent("400");
    expect(screen.getByTestId("game-record")).toBeInTheDocument();
    expect(screen.getByTestId("game-review-note")).toHaveTextContent("3 thẻ đến hạn");
  });

  it("ghép sai một lần: thẻ đó được ghi 1 lần sai", async () => {
    await playAll(true);
    await screen.findByTestId("game-result", {}, { timeout: 3000 });
    const first = lastSubmit().items.find((i: any) => i.card_id === "c1");
    expect(first).toMatchObject({ correct: true, attempts: 1 });
  });

  it("tắt 'Tính vào lịch ôn' thì gửi apply_review=false", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("match", four));
    renderHub();
    fireEvent.click(await screen.findByLabelText(/Tính vào lịch ôn/));
    await startGame("match");
    for (const n of [1, 2, 3, 4]) {
      fireEvent.click(screen.getByTestId(`match-term-c${n}`));
      fireEvent.click(screen.getByTestId(`match-def-c${n}`));
    }
    await screen.findByTestId("game-result", {}, { timeout: 3000 });
    expect(lastSubmit().applyReview).toBe(false);
  });

  it("thoát giữa chừng thì không gửi gì", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("match", four));
    renderHub();
    await startGame("match");
    fireEvent.click(screen.getByTestId("match-term-c1"));
    fireEvent.click(screen.getByRole("button", { name: /Thoát ván/ }));
    expect(await screen.findByTestId("game-card-match")).toBeInTheDocument();
    expect(svc.submitGameSession).not.toHaveBeenCalled();
  });

  it("gửi kết quả lỗi: báo rõ, 'Thử gửi lại' dùng CÙNG client_request_id", async () => {
    svc.submitGameSession.mockResolvedValueOnce({ ok: false, error: { message: "Mất kết nối" } });
    await playAll();
    expect(await screen.findByRole("alert", {}, { timeout: 3000 })).toHaveTextContent("Chưa lưu được kết quả");
    const firstId = lastSubmit().clientRequestId;
    fireEvent.click(screen.getByRole("button", { name: "Thử gửi lại" }));
    expect(await screen.findByTestId("game-result")).toBeInTheDocument();
    expect(svc.submitGameSession).toHaveBeenCalledTimes(2);
    expect(lastSubmit().clientRequestId).toBe(firstId);
  });

  it("'Chơi lại' tải ván mới", async () => {
    await playAll();
    await screen.findByTestId("game-result", {}, { timeout: 3000 });
    fireEvent.click(screen.getByRole("button", { name: /Chơi lại/ }));
    await waitFor(() => expect(svc.fetchGameCards).toHaveBeenCalledTimes(2));
    expect(await screen.findByTestId("match-progress")).toHaveTextContent("Đã ghép 0/4");
  });
});

describe("Đua 60 giây", () => {
  const five = [1, 2, 3, 4, 5].map((n) => gcard(n));

  it("Thư giãn: 10 câu, trả lời hết thì gửi 10 kết quả; chọn sai ở chế độ này chờ bấm Tiếp tục", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"] });
    svc.fetchGameCards.mockResolvedValue(cardsData("speed", five));
    renderHub();
    await act(async () => {});
    fireEvent.click(screen.getByTestId("game-card-speed"));
    await act(async () => {});

    for (let i = 0; i < 10; i++) {
      const term = screen.getByTestId("speed-term").textContent!;
      const n = Number(term.replace("word", ""));
      const wrong = i === 3;
      const group = screen.getByRole("group", { name: "Các đáp án" });
      fireEvent.click(within(group).getByText(wrong ? "sai A" : `nghĩa ${n}`));
      if (wrong) {
        fireEvent.click(screen.getByRole("button", { name: /Tiếp tục/ }));
      } else {
        await act(async () => { vi.advanceTimersByTime(700); });
      }
    }
    await act(async () => {});
    expect(screen.getByTestId("game-result")).toBeInTheDocument();
    const { items } = lastSubmit();
    expect(items).toHaveLength(10);
    expect(items.filter((x: any) => !x.correct)).toHaveLength(1);
    expect(items[3]).toMatchObject({ correct: false, attempts: 1 });
  });

  it("Thử thách: sai 3 lần thì kết thúc ván (hết mạng)", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"] });
    svc.fetchGameCards.mockResolvedValue(cardsData("speed", five));
    renderHub();
    await act(async () => {});
    fireEvent.click(screen.getByRole("radio", { name: /Thử thách/ }));
    fireEvent.click(screen.getByTestId("game-card-speed"));
    await act(async () => {});
    expect(screen.getByTestId("speed-lives")).toBeInTheDocument();

    for (let i = 0; i < 3; i++) {
      fireEvent.click(within(screen.getByRole("group", { name: "Các đáp án" })).getByText("sai A"));
      await act(async () => { vi.advanceTimersByTime(1100); });
    }
    await act(async () => {});
    expect(screen.getByTestId("game-result")).toBeInTheDocument();
    expect(lastSubmit()).toMatchObject({ mode: "challenge" });
    expect(lastSubmit().items).toHaveLength(3);
  });

  it("Thử thách: hết 60 giây thì kết thúc", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"] });
    svc.fetchGameCards.mockResolvedValue(cardsData("speed", five));
    renderHub();
    await act(async () => {});
    fireEvent.click(screen.getByRole("radio", { name: /Thử thách/ }));
    fireEvent.click(screen.getByTestId("game-card-speed"));
    await act(async () => {});
    const n = Number(screen.getByTestId("speed-term").textContent!.replace("word", ""));
    fireEvent.click(within(screen.getByRole("group", { name: "Các đáp án" })).getByText(`nghĩa ${n}`));
    await act(async () => { vi.advanceTimersByTime(61_000); });
    await act(async () => {});
    expect(screen.getByTestId("game-result")).toBeInTheDocument();
    expect(lastSubmit().items).toHaveLength(1);
  });

  it("phím 1–4 chọn đáp án", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("speed", five));
    renderHub();
    await startGame("speed");
    fireEvent.keyDown(window, { key: "1" });
    await waitFor(() => expect(screen.getByTestId("speed-combo")).toBeInTheDocument());
    const group = screen.getByRole("group", { name: "Các đáp án" });
    expect(within(group).getAllByRole("button").every((b) => (b as HTMLButtonElement).disabled)).toBe(true); // đã trả lời
  });
});

describe("Xếp chữ", () => {
  const words = ["haus", "baum", "tuer", "hund"].map((w, i) => gcard(i + 1, w, "de"));

  const typeCurrentWord = () => {
    const meaning = screen.getByTestId("builder-meaning").textContent!;
    const card = words.find((w) => w.definition === meaning)!;
    for (const ch of Array.from(card.term)) fireEvent.keyDown(window, { key: ch });
    return card;
  };

  it("gõ đúng từng từ, Enter sang từ kế, xong thì gửi kết quả", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("builder", words, { lang_code: "de" }));
    renderHub(deckOf("de"));
    await startGame("builder");
    for (let i = 0; i < 4; i++) {
      expect(screen.getByTestId("builder-progress")).toHaveTextContent(`Từ ${i + 1}/4`);
      typeCurrentWord();
      await screen.findByRole("status");
      fireEvent.keyDown(window, { key: "Enter" });
    }
    expect(await screen.findByTestId("game-result")).toBeInTheDocument();
    expect(lastSubmit()).toMatchObject({ game: "builder" });
    expect(lastSubmit().items).toHaveLength(4);
    expect(lastSubmit().items.every((i: any) => i.correct && i.hints === 0 && i.attempts === 0)).toBe(true);
  });

  it("gợi ý và bỏ qua được ghi nhận", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("builder", words, { lang_code: "de" }));
    renderHub(deckOf("de"));
    await startGame("builder");
    fireEvent.click(screen.getByRole("button", { name: /Gợi ý \(3\)/ }));
    expect(screen.getByRole("button", { name: /Gợi ý \(2\)/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Bỏ qua/ }));
    expect(screen.getByTestId("builder-progress")).toHaveTextContent("Từ 2/4");
    for (let i = 0; i < 3; i++) {
      typeCurrentWord();
      await screen.findByRole("status");
      fireEvent.keyDown(window, { key: "Enter" });
    }
    await screen.findByTestId("game-result");
    const items = lastSubmit().items;
    expect(items).toHaveLength(4);
    expect(items.filter((i: any) => !i.correct)).toHaveLength(1);
    expect(items.find((i: any) => !i.correct)).toMatchObject({ hints: 1 });
  });

  it("xếp sai: rung, xóa và tính một lỗi", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("builder", words, { lang_code: "de" }));
    renderHub(deckOf("de"));
    await startGame("builder");
    const meaning = screen.getByTestId("builder-meaning").textContent!;
    const card = words.find((w) => w.definition === meaning)!;
    const wrongOrder = Array.from(card.term).reverse();
    if (wrongOrder.join("") === card.term) return; // từ đối xứng: không có thứ tự sai để thử
    for (const ch of wrongOrder) fireEvent.keyDown(window, { key: ch });
    await act(async () => { await new Promise((r) => setTimeout(r, 800)); });
    typeCurrentWord();
    await screen.findByRole("status");
    fireEvent.keyDown(window, { key: "Enter" });
    for (let i = 0; i < 3; i++) {
      typeCurrentWord();
      await screen.findByRole("status");
      fireEvent.keyDown(window, { key: "Enter" });
    }
    await screen.findByTestId("game-result");
    expect(lastSubmit().items.find((i: any) => i.card_id === card.id)).toMatchObject({ correct: true, attempts: 1 });
  });
});


describe("Bắn bóng nghĩa trong GamesHub", () => {
  const five = [1, 2, 3, 4, 5].map((n) => gcard(n));

  it("thẻ thứ tư xuất hiện, dùng được với mọi ngôn ngữ (kể cả tiếng Nhật)", async () => {
    renderHub(deckOf("ja"));
    await screen.findByText("Cấp 1");
    expect(screen.getByTestId("game-card-shooter")).toBeEnabled();
    expect(screen.getByTestId("game-card-shooter")).toHaveTextContent("Bắn bóng nghĩa");
  });

  it("sổ chưa đủ 5 thẻ: hiện lý do từ máy chủ", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("shooter", [], { playable: false, min_required: 5, reason: "Cần ít nhất 5 thẻ có từ và nghĩa khác nhau trong sổ này để chơi (hiện có 4)." }));
    renderHub();
    fireEvent.click(await screen.findByTestId("game-card-shooter"));
    expect(await screen.findByTestId("games-menu-error")).toHaveTextContent("Cần ít nhất 5");
    expect(svc.fetchGameCards).toHaveBeenCalledWith("shooter", "deck-1");
  });

  it("vào ván và hiện súng + bóng; thoát về menu không gửi gì", async () => {
    svc.fetchGameCards.mockResolvedValue(cardsData("shooter", five));
    renderHub();
    await startGame("shooter");
    expect(await screen.findByTestId("shooter-arena")).toBeInTheDocument();
    expect(screen.getByTestId("shooter-word")).toHaveTextContent(/^word\d$/);
    fireEvent.click(screen.getByRole("button", { name: /Thoát ván/ }));
    expect(await screen.findByTestId("game-card-shooter")).toBeInTheDocument();
    expect(svc.submitGameSession).not.toHaveBeenCalled();
  });

  it("hiện kỷ lục riêng của trò theo chế độ", async () => {
    svc.fetchGameStats.mockResolvedValue({
      ok: true,
      data: emptyStats({ games: { match: { plays: 0, last_played: null, best: { relax: null, challenge: null } }, speed: { plays: 0, last_played: null, best: { relax: null, challenge: null } },
        builder: { plays: 0, last_played: null, best: { relax: null, challenge: null } }, shooter: { plays: 2, last_played: null, best: { relax: { score: 120, stars: 2, best_combo: 4 }, challenge: null } } } })
    });
    renderHub();
    expect(await screen.findByTestId("game-best-shooter")).toHaveTextContent("Kỷ lục 120");
  });
});
