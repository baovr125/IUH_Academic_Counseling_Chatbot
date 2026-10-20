import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

const svc = vi.hoisted(() => ({
  fetchLanguageSummary: vi.fn(),
  fetchLanguageCards: vi.fn(),
  fetchBackendDecks: vi.fn(),
  setDeckLanguage: vi.fn(),
  fetchDeckCards: vi.fn(),
  fetchStudyQueue: vi.fn(),
  fetchStudyStats: vi.fn(),
  fetchReviewStreak: vi.fn()
}));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "user-1" } }) }));

import { LanguageSelectionGrid } from "../src/components/flashcards/LanguageSelectionGrid";
import { UnconfirmedDecks } from "../src/components/flashcards/UnconfirmedDecks";
import FlashcardPage from "../src/pages/FlashcardPage";
import { LANG_CODES } from "../src/services/deckStorage";
import type { LanguageSummary } from "../src/services/flashcardService";

const item = (code: string, over: Record<string, unknown> = {}) => ({
  code, learnable: code !== "vi", decks: 0, cards: 0, new: 0, due: 0, weak: 0, ...over
});
const summaryOf = (over: Record<string, Record<string, unknown>> = {}, unconfirmed: LanguageSummary["unconfirmed"] = { decks: [], cards: 0 }): LanguageSummary => ({
  languages: LANG_CODES.map((c) => item(c, over[c])) as any,
  unconfirmed
});

describe("LanguageSelectionGrid — chọn 1 trong 10 ngôn ngữ", () => {
  const renderGrid = (props: Partial<React.ComponentProps<typeof LanguageSelectionGrid>> = {}) => {
    const onSelect = vi.fn();
    const onRetry = vi.fn();
    render(<LanguageSelectionGrid summary={summaryOf()} isLoading={false} isError={false} onRetry={onRetry} onSelect={onSelect} {...props} />);
    return { onSelect, onRetry };
  };

  it("hiển thị đủ 10 thẻ ngôn ngữ (cờ + tên), ban đầu chưa có từ vựng nào", () => {
    renderGrid();
    const grid = screen.getByTestId("language-grid");
    expect(within(grid).getAllByRole("button")).toHaveLength(10);
    for (const name of ["Tiếng Anh", "Tiếng Đức", "Tiếng Trung", "Tiếng Nhật", "Tiếng Hàn", "Tiếng Pháp", "Tiếng Tây Ban Nha", "Tiếng Nga", "Tiếng Thái", "Tiếng Việt"]) {
      expect(within(grid).getByText(name)).toBeInTheDocument();
    }
    expect(within(grid).getAllByText("Chưa có từ vựng")).toHaveLength(9);
  });

  it.each(LANG_CODES.filter((c) => c !== "vi"))("bấm vào %s gọi onSelect với đúng mã ISO", (code) => {
    const { onSelect } = renderGrid();
    fireEvent.click(screen.getByTestId(`lang-card-${code}`));
    expect(onSelect).toHaveBeenCalledWith(code);
  });

  it("tiếng Việt bị khóa kèm giải thích, không chọn được", () => {
    const { onSelect } = renderGrid();
    const vi_ = screen.getByTestId("lang-card-vi");
    expect(vi_).toHaveAttribute("aria-disabled", "true");
    expect(vi_).toHaveTextContent(/ngôn ngữ giải nghĩa/i);
    fireEvent.click(vi_);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("tiếng Việt chỉ mở khi còn sổ cũ mang mã 'vi'", () => {
    const { onSelect } = renderGrid({ summary: summaryOf({ vi: { decks: 1, cards: 4 } }) });
    expect(screen.getByTestId("lang-card-vi")).toHaveAttribute("aria-disabled", "false");
    fireEvent.click(screen.getByTestId("lang-card-vi"));
    expect(onSelect).toHaveBeenCalledWith("vi");
  });

  it("hiển thị số từ, số sổ và số thẻ cần ôn của từng ngôn ngữ", () => {
    renderGrid({ summary: summaryOf({ de: { decks: 2, cards: 12, due: 3 }, ja: { decks: 1, cards: 1 } }) });
    expect(screen.getByTestId("lang-card-de")).toHaveTextContent("12 từ • 2 sổ");
    expect(screen.getByTestId("lang-card-de")).toHaveTextContent("3 cần ôn");
    expect(screen.getByTestId("lang-card-ja")).toHaveTextContent("1 từ • 1 sổ");
    expect(screen.getByTestId("lang-card-en")).toHaveTextContent("Chưa có từ vựng");
  });

  it("đang tải: vẫn có đủ 10 thẻ (skeleton), lỗi: báo lỗi + Thử lại nhưng vẫn chọn được ngôn ngữ", () => {
    renderGrid({ summary: undefined, isLoading: true });
    expect(screen.getAllByRole("button")).toHaveLength(10);

    const { onSelect, onRetry } = renderGrid({ summary: undefined, isError: true, errorMessage: "Mất kết nối" });
    expect(screen.getByRole("alert")).toHaveTextContent("Mất kết nối");
    fireEvent.click(screen.getByRole("button", { name: /Thử lại/ }));
    expect(onRetry).toHaveBeenCalled();
    const frCards = screen.getAllByTestId("lang-card-fr");
    fireEvent.click(frCards[frCards.length - 1]);
    expect(onSelect).toHaveBeenCalledWith("fr");
  });
});

describe("UnconfirmedDecks — dữ liệu cũ không bị đoán ngôn ngữ", () => {
  beforeEach(() => svc.setDeckLanguage.mockReset());

  it("không hiện gì khi không có sổ chưa xác nhận", () => {
    const { container } = render(<UnconfirmedDecks decks={[]} onOpenDeck={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("phải chọn ngôn ngữ mới xác nhận được; gọi API đúng sổ + mã ngôn ngữ", async () => {
    svc.setDeckLanguage.mockResolvedValue({ ok: true, data: {} });
    render(<UnconfirmedDecks decks={[{ id: "d1", title: "Sổ cũ", lang_code: "en", cards_count: 5 }]} onOpenDeck={vi.fn()} />);
    const confirm = screen.getByRole("button", { name: "Xác nhận" });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Ngôn ngữ của sổ Sổ cũ/), { target: { value: "de" } });
    fireEvent.click(confirm);
    await waitFor(() => expect(svc.setDeckLanguage).toHaveBeenCalledWith("d1", "de"));
  });

  it("hiển thị lỗi khi máy chủ từ chối", async () => {
    svc.setDeckLanguage.mockResolvedValue({ ok: false, error: { message: "Không có quyền" } });
    render(<UnconfirmedDecks decks={[{ id: "d1", title: "Sổ cũ", cards_count: 1 }]} onOpenDeck={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Ngôn ngữ của sổ/), { target: { value: "ja" } });
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Không có quyền");
  });
});

// ---- Điều hướng toàn trang -------------------------------------------------------
function Where() {
  const loc = useLocation();
  return <div data-testid="where">{loc.pathname + loc.search}</div>;
}

function renderPage(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Where />
        <Routes>
          <Route path="/flashcards" element={<FlashcardPage />} />
          <Route path="/flashcards/:lang" element={<FlashcardPage />} />
          <Route path="/flashcards/:lang/decks/:deckId" element={<FlashcardPage />} />
          <Route path="/translation" element={<div>TRANSLATION PAGE</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const cardRow = (n: number, over: Record<string, unknown> = {}) => ({
  id: `c${n}`, deck_id: "d1", term: `Wort${n}`, definition: `từ ${n}`, lang_code: "de", deck_title: "Từ vựng Tiếng Đức", state: 0, ...over
});

beforeEach(() => {
  localStorage.clear();
  Object.values(svc).forEach((m) => m.mockReset());
  svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ de: { decks: 1, cards: 2, default_deck_id: "d1" } }) });
  svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [{ id: "d1", title: "Từ vựng Tiếng Đức", lang_code: "de", lang_confirmed: true, cards_count: 2, is_default: true }] });
  svc.fetchLanguageCards.mockResolvedValue({ ok: true, data: { items: [cardRow(1), cardRow(2)], total: 2, limit: 20, offset: 0 } });
  svc.fetchReviewStreak.mockResolvedValue({ ok: false, error: { message: "offline" } });
  svc.fetchDeckCards.mockResolvedValue({ ok: true, data: [] });
  svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [] });
  svc.fetchStudyStats.mockResolvedValue({ ok: true, data: { total: 0, new: 0, due: 0, learning: 0, mastered: 0, weak: 0 } });
});

describe("FlashcardPage — điều hướng theo ngôn ngữ", () => {
  it("/flashcards hiển thị màn chọn 10 ngôn ngữ, chưa liệt kê thẻ nào", async () => {
    renderPage("/flashcards");
    expect(await screen.findByRole("heading", { name: /Chọn ngôn ngữ để học/i })).toBeInTheDocument();
    expect(screen.getAllByTestId(/^lang-card-/)).toHaveLength(10);
    expect(svc.fetchLanguageCards).not.toHaveBeenCalled();
    expect(svc.fetchBackendDecks).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByTestId("lang-card-de")).toHaveTextContent("2 từ"));
  });

  it("chọn Tiếng Đức -> /flashcards/de, chỉ tải sổ của tiếng Đức (lọc ở máy chủ)", async () => {
    renderPage("/flashcards");
    fireEvent.click(await screen.findByTestId("lang-card-de"));
    expect(await screen.findByRole("heading", { name: "Tiếng Đức" })).toBeInTheDocument();
    expect(screen.getByTestId("where")).toHaveTextContent("/flashcards/de");
    await waitFor(() => expect(svc.fetchBackendDecks).toHaveBeenCalledWith("de"));
    expect(await screen.findByText("Từ vựng Tiếng Đức", { selector: "h3" })).toBeInTheDocument();
  });

  it("nút 'Tất cả ngôn ngữ' quay về màn chọn", async () => {
    renderPage("/flashcards/de");
    fireEvent.click(await screen.findByRole("button", { name: /Tất cả ngôn ngữ/ }));
    expect(await screen.findByRole("heading", { name: /Chọn ngôn ngữ để học/i })).toBeInTheDocument();
    expect(screen.getByTestId("where")).toHaveTextContent(/^\/flashcards$/);
  });

  it("tab 'Tất cả từ vựng' lấy từ vựng của đúng ngôn ngữ từ máy chủ", async () => {
    renderPage("/flashcards/de");
    fireEvent.click(await screen.findByRole("tab", { name: "Tất cả từ vựng" }));
    expect(await screen.findByText("Wort1")).toBeInTheDocument();
    expect(svc.fetchLanguageCards).toHaveBeenCalledWith("de", expect.objectContaining({ sort: "recent", status: "all", limit: 20, offset: 0 }));
    expect(screen.getByTestId("where")).toHaveTextContent("?tab=words");
  });

  it("tìm kiếm / lọc / sắp xếp được gửi lên máy chủ", async () => {
    renderPage("/flashcards/de?tab=words");
    await screen.findByText("Wort1");

    fireEvent.change(screen.getByLabelText("Tìm từ vựng"), { target: { value: "haus" } });
    await waitFor(() => expect(svc.fetchLanguageCards).toHaveBeenLastCalledWith("de", expect.objectContaining({ q: "haus" })));

    fireEvent.click(screen.getByRole("button", { name: "Cần ôn" }));
    await waitFor(() => expect(svc.fetchLanguageCards).toHaveBeenLastCalledWith("de", expect.objectContaining({ status: "due", q: "haus" })));

    fireEvent.change(screen.getByLabelText("Sắp xếp"), { target: { value: "alpha" } });
    await waitFor(() => expect(svc.fetchLanguageCards).toHaveBeenLastCalledWith("de", expect.objectContaining({ sort: "alpha", status: "due", q: "haus" })));
  });

  it("phân trang dùng offset ở máy chủ", async () => {
    svc.fetchLanguageCards.mockResolvedValue({ ok: true, data: { items: [cardRow(1)], total: 45, limit: 20, offset: 0 } });
    renderPage("/flashcards/de?tab=words");
    await screen.findByText("Wort1");
    expect(screen.getByText(/Hiển thị 1–20 \/ 45 từ/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Trang sau" }));
    await waitFor(() => expect(svc.fetchLanguageCards).toHaveBeenLastCalledWith("de", expect.objectContaining({ offset: 20 })));
  });

  it("ngôn ngữ chưa có từ nào: trạng thái rỗng kèm lối đi sang Dịch thuật", async () => {
    svc.fetchLanguageCards.mockResolvedValue({ ok: true, data: { items: [], total: 0, limit: 20, offset: 0 } });
    svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [] });
    renderPage("/flashcards/ko?tab=words");
    const empty = await screen.findByTestId("words-empty");
    expect(empty).toHaveTextContent("Chưa có từ vựng Tiếng Hàn nào");
    fireEvent.click(within(empty).getByRole("button", { name: /Mở Dịch thuật/ }));
    expect(await screen.findByText("TRANSLATION PAGE")).toBeInTheDocument();
  });

  it("tìm không thấy: thông báo khác với trạng thái rỗng ban đầu", async () => {
    renderPage("/flashcards/de?tab=words");
    await screen.findByText("Wort1");
    svc.fetchLanguageCards.mockResolvedValue({ ok: true, data: { items: [], total: 0, limit: 20, offset: 0 } });
    fireEvent.change(screen.getByLabelText("Tìm từ vựng"), { target: { value: "zzz" } });
    expect(await screen.findByText("Không tìm thấy từ nào")).toBeInTheDocument();
  });

  it("lỗi tải từ vựng: hiện thông báo và nút thử lại", async () => {
    svc.fetchLanguageCards.mockResolvedValue({ ok: false, error: { message: "Máy chủ bận" } });
    renderPage("/flashcards/de?tab=words");
    expect(await screen.findByRole("alert")).toHaveTextContent("Máy chủ bận");
  });

  it("mã ngôn ngữ sai trên URL (kể cả mã cờ 'jp') quay về màn chọn", async () => {
    renderPage("/flashcards/jp");
    expect(await screen.findByRole("heading", { name: /Chọn ngôn ngữ để học/i })).toBeInTheDocument();
    expect(screen.getByTestId("where")).toHaveTextContent(/^\/flashcards$/);
  });

  it("trình sinh từ AI dùng được cho tiếng Đức, còn thư viện bộ từ chỉ có ở tiếng Anh", async () => {
    renderPage("/flashcards/de");
    await screen.findByText("Từ vựng Tiếng Đức", { selector: "h3" });
    expect(screen.getByRole("button", { name: /Tạo từ vựng với AI/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Thư viện bộ từ/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Tạo sổ Tiếng Đức mới/ })).toBeInTheDocument();
  });

  it("tiếng Anh vẫn có công cụ AI và thư viện bộ từ", async () => {
    svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [] });
    renderPage("/flashcards/en");
    expect(await screen.findAllByRole("button", { name: /Tạo từ vựng với AI/ })).not.toHaveLength(0);
    expect(screen.getAllByRole("button", { name: /Thư viện bộ từ/ }).length).toBeGreaterThan(0);
  });

  it("mở một sổ -> /flashcards/de/decks/:id, nút quay lại về bộ sưu tập", async () => {
    renderPage("/flashcards/de");
    fireEvent.click(await screen.findByText("Từ vựng Tiếng Đức", { selector: "h3" }));
    await waitFor(() => expect(screen.getByTestId("where")).toHaveTextContent("/flashcards/de/decks/d1"));
    fireEvent.click(await screen.findByRole("button", { name: /Sổ thẻ Tiếng Đức/ }));
    await waitFor(() => expect(screen.getByTestId("where")).toHaveTextContent(/^\/flashcards\/de$/));
  });

  it("sổ không tồn tại / không thuộc ngôn ngữ trên URL: báo không tìm thấy", async () => {
    renderPage("/flashcards/de/decks/khong-co");
    expect(await screen.findByText("Không tìm thấy sổ thẻ")).toBeInTheDocument();
  });
});
