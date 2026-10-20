import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

const svc = vi.hoisted(() => ({
  fetchLanguageSummary: vi.fn(),
  fetchBackendDecks: vi.fn(),
  fetchDeckCards: vi.fn(),
  fetchStudyQueue: vi.fn(),
  fetchStudyStats: vi.fn(),
  fetchReviewStreak: vi.fn(),
  deleteBackendCard: vi.fn()
}));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
vi.mock("../src/services/settingsService", () => ({
  fetchUserSettings: vi.fn(async () => ({ ok: false, error: { message: "x" } })),
  updateUserSettings: vi.fn(async () => ({ ok: true, data: {} }))
}));
vi.mock("../src/hooks/useAuth", async (orig) => ({ ...(await orig<object>()), useAuth: () => ({ user: { id: "user-1" } }) }));
// Virtuoso cần kích thước thật của khung nhìn nên không render được mục nào trong jsdom: thay bằng danh sách phẳng.
vi.mock("react-virtuoso", () => ({
  Virtuoso: ({ totalCount, itemContent }: { totalCount: number; itemContent: (i: number) => React.ReactNode }) => (
    <div>{Array.from({ length: totalCount }, (_, i) => <div key={i}>{itemContent(i)}</div>)}</div>
  )
}));

import FlashcardPage from "../src/pages/FlashcardPage";
import { ConfirmDialog } from "../src/components/flashcards/ConfirmDialog";
import { SessionSummary, formatClock } from "../src/components/flashcards/SessionSummary";
import { FcMenu } from "../src/components/flashcards/ui";
import { SettingsProvider } from "../src/context/SettingsContext";

// ---------------------------------------------------------------------------------------------------------------
describe("FcMenu — nút chữ có mũi tên", () => {
  it("dùng nhãn nhìn thấy làm tên nút, mở menu và gọi đúng hành động", () => {
    const onAdd = vi.fn();
    render(<FcMenu label="Thêm từ vào sổ" buttonLabel="Thêm từ vựng" items={[{ key: "a", label: "Thêm một từ", onClick: onAdd }]} />);
    const trigger = screen.getByRole("button", { name: "Thêm từ vựng" });
    expect(trigger).toHaveAttribute("aria-haspopup", "menu");
    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    fireEvent.click(screen.getByRole("menuitem", { name: "Thêm một từ" }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it("phím ↓ trên nút đang đóng thì mở menu", () => {
    render(<FcMenu label="m" buttonLabel="Mở" items={[{ key: "a", label: "A", onClick: vi.fn() }]} />);
    fireEvent.keyDown(screen.getByRole("button", { name: "Mở" }), { key: "ArrowDown" });
    expect(screen.getByRole("menu")).toBeInTheDocument();
  });
});

describe("ConfirmDialog", () => {
  const renderDialog = (props: Partial<React.ComponentProps<typeof ConfirmDialog>> = {}) => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <SettingsProvider>
        <ConfirmDialog title="Xóa thẻ từ vựng" message="Không thể hoàn tác." confirmLabel="Xóa thẻ" onConfirm={onConfirm} onCancel={onCancel} {...props} />
      </SettingsProvider>
    );
    return { onConfirm, onCancel };
  };

  it("là hộp thoại có tên, xác nhận và hủy gọi đúng hàm", () => {
    const { onConfirm, onCancel } = renderDialog();
    const dialog = screen.getByRole("dialog", { name: "Xóa thẻ từ vựng" });
    expect(within(dialog).getByText("Không thể hoàn tác.")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "Hủy" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
    fireEvent.click(within(dialog).getByRole("button", { name: "Xóa thẻ" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("Esc đóng hộp thoại", () => {
    const { onCancel } = renderDialog();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("đang xử lý: khóa cả hai nút và Esc không đóng", () => {
    const { onCancel } = renderDialog({ isLoading: true });
    expect(screen.getByRole("button", { name: "Hủy" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Xóa thẻ" })).toBeDisabled();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).not.toHaveBeenCalled();
  });
});

describe("SessionSummary", () => {
  it("formatClock hiển thị m:ss và tối thiểu 0:01", () => {
    expect(formatClock(65_000)).toBe("1:05");
    expect(formatClock(7_000)).toBe("0:07");
    expect(formatClock(0)).toBe("0:01");
  });

  it("hiện số thẻ, độ chính xác, thời gian và tiến độ ghi nhớ của sổ", () => {
    const results = [
      { cardId: "a", term: "x", definition: "một", grade: 3, correct: true, ms: 1000 },
      { cardId: "b", term: "y", definition: "hai", grade: 1, correct: false, ms: 1000 },
      { cardId: "c", term: "z", definition: "ba", grade: 4, correct: true, ms: 1000 },
      { cardId: "d", term: "w", definition: "bốn", grade: 3, correct: true, ms: 1000 }
    ];
    render(
      <SessionSummary
        results={results}
        durationMs={125_000}
        stats={{ total: 10, new: 1, due: 2, learning: 4, mastered: 5, weak: 1 }}
        onPlayAudio={vi.fn()}
        onRetryWeak={vi.fn()}
        onNextSession={vi.fn()}
        onBack={vi.fn()}
      />
    );
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("2:05")).toBeInTheDocument();
    expect(screen.getByText("5/10 đã thuộc")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Làm tốt lắm!" })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------------------------------
function Where() {
  const loc = useLocation();
  return <div data-testid="where">{loc.pathname + loc.search}</div>;
}

function renderDeck(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <SettingsProvider>
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={[path]}>
          <Where />
          <Routes>
            <Route path="/flashcards" element={<FlashcardPage />} />
            <Route path="/flashcards/:lang" element={<FlashcardPage />} />
            <Route path="/flashcards/:lang/decks/:deckId" element={<FlashcardPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </SettingsProvider>
  );
}

const cardRow = (n: number) => ({ id: `c${n}`, deck_id: "d1", term: `Wort${n}`, definition: `từ ${n}`, lang_code: "de", state: 0 });
const deckOf = (over: Record<string, unknown> = {}) => ({
  id: "d1", title: "Từ vựng Tiếng Đức", description: "Bộ từ cơ bản", lang_code: "de", lang_confirmed: true, cards_count: 2, is_default: true, ...over
});

beforeEach(() => {
  localStorage.clear();
  Object.values(svc).forEach((m) => m.mockReset());
  svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: { languages: [], unconfirmed: { decks: [], cards: 0 } } });
  svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [deckOf()] });
  svc.fetchDeckCards.mockResolvedValue({ ok: true, data: [cardRow(1), cardRow(2)] });
  svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [] });
  svc.fetchStudyStats.mockResolvedValue({ ok: true, data: { total: 2, new: 2, due: 0, learning: 0, mastered: 0, weak: 0 } });
  svc.fetchReviewStreak.mockResolvedValue({ ok: false, error: { message: "offline" } });
  svc.deleteBackendCard.mockResolvedValue({ ok: true, data: { deleted: true } });
});

describe("FlashcardPage — chi tiết sổ", () => {
  it("header: breadcrumb về bộ sưu tập, h1 là tên sổ, số thẻ và huy hiệu Mặc định", async () => {
    renderDeck("/flashcards/de/decks/d1");
    expect(await screen.findByRole("heading", { level: 1, name: "Từ vựng Tiếng Đức" })).toBeInTheDocument();
    expect(screen.getByText("Bộ từ cơ bản")).toBeInTheDocument();
    expect(screen.getByText("Mặc định")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("2 thẻ")).toBeInTheDocument());
    const nav = screen.getByRole("navigation", { name: "Đường dẫn" });
    expect(within(nav).getByText("Từ vựng Tiếng Đức")).toHaveAttribute("aria-current", "page");
    fireEvent.click(within(nav).getByRole("button", { name: /Sổ thẻ Tiếng Đức/ }));
    await waitFor(() => expect(screen.getByTestId("where")).toHaveTextContent(/^\/flashcards\/de$/));
  });

  it("3 tab: Ôn tập mặc định, Danh sách có số thẻ, Trò chơi; chuyển tab đổi nội dung", async () => {
    renderDeck("/flashcards/de/decks/d1");
    const study = await screen.findByRole("tab", { name: /Ôn tập FSRS/ });
    expect(study).toHaveAttribute("aria-selected", "true");
    const list = await screen.findByRole("tab", { name: /Danh sách\s*2/ });
    fireEvent.click(list);
    expect(list).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText("Wort1")).toBeInTheDocument();
    expect(screen.getByText(/Hiển thị/)).toHaveTextContent("2 / 2 thẻ từ vựng");
    expect(screen.getByRole("tab", { name: /Trò chơi/ })).toBeInTheDocument();
  });

  it("menu Thêm từ vựng: tiếng Đức cũng có 'Tạo thêm bằng AI' (AI dùng được cho cả 9 ngôn ngữ học)", async () => {
    renderDeck("/flashcards/de/decks/d1");
    fireEvent.click(await screen.findByRole("button", { name: "Thêm từ vựng" }));
    expect(screen.getAllByRole("menuitem").map((i) => i.textContent)).toEqual(["Thêm một từ", "Nhập từ Excel / CSV", "Tạo thêm bằng AI"]);
  });

  it("sổ tiếng Việt cũ (ngôn ngữ giải nghĩa) không có mục AI", async () => {
    svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [deckOf({ lang_code: "vi", title: "Sổ cũ" })] });
    renderDeck("/flashcards/vi/decks/d1");
    fireEvent.click(await screen.findByRole("button", { name: "Thêm từ vựng" }));
    expect(screen.getAllByRole("menuitem").map((i) => i.textContent)).toEqual(["Thêm một từ", "Nhập từ Excel / CSV"]);
  });

  it("menu Thêm từ vựng: tiếng Anh có thêm 'Tạo thêm bằng AI'", async () => {
    svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [deckOf({ lang_code: "en", title: "English deck" })] });
    renderDeck("/flashcards/en/decks/d1");
    fireEvent.click(await screen.findByRole("button", { name: "Thêm từ vựng" }));
    expect(screen.getAllByRole("menuitem").map((i) => i.textContent)).toEqual(["Thêm một từ", "Nhập từ Excel / CSV", "Tạo thêm bằng AI"]);
  });

  it("xóa thẻ: hộp thoại trong ứng dụng (không dùng window.confirm), hủy thì không xóa", async () => {
    const nativeConfirm = vi.spyOn(window, "confirm");
    renderDeck("/flashcards/de/decks/d1");
    fireEvent.click(await screen.findByRole("tab", { name: /Danh sách/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Xóa thẻ Wort1" }));

    const dialog = await screen.findByRole("dialog", { name: "Xóa thẻ từ vựng" });
    expect(dialog).toHaveTextContent("“Wort1”");
    fireEvent.click(within(dialog).getByRole("button", { name: "Hủy" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(svc.deleteBackendCard).not.toHaveBeenCalled();
    expect(nativeConfirm).not.toHaveBeenCalled();
    nativeConfirm.mockRestore();
  });

  it("xóa thẻ: xác nhận thì gọi API đúng thẻ và đóng hộp thoại", async () => {
    renderDeck("/flashcards/de/decks/d1");
    fireEvent.click(await screen.findByRole("tab", { name: /Danh sách/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Xóa thẻ Wort2" }));
    const dialog = await screen.findByRole("dialog", { name: "Xóa thẻ từ vựng" });
    fireEvent.click(within(dialog).getByRole("button", { name: "Xóa thẻ" }));
    await waitFor(() => expect(svc.deleteBackendCard).toHaveBeenCalledWith("c2"));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("sổ chưa xác nhận ngôn ngữ hiện ghi chú cảnh báo", async () => {
    svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [deckOf({ lang_confirmed: false })] });
    renderDeck("/flashcards/unconfirmed/decks/d1");
    expect(await screen.findByRole("note")).toHaveTextContent(/chưa được xác nhận/);
    expect(screen.getByRole("button", { name: /Quay lại Sổ thẻ/ })).toBeInTheDocument();
  });
});
