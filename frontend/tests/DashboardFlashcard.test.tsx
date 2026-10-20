import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

const svc = vi.hoisted(() => ({ fetchLanguageSummary: vi.fn(), fetchReviewStreak: vi.fn() }));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
const auth = vi.hoisted(() => ({ user: { id: "user-1" } as { id: string } | null }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: auth.user }) }));

import { FlashcardDueCard } from "../src/components/dashboard/FlashcardDueCard";
import { PublicLearningProductivityCard } from "../src/components/dashboard/PublicLearningProductivityCard";
import { SampleDataBadge } from "../src/components/dashboard/SampleDataBadge";
import { buildFlashcardOverview } from "../src/hooks/flashcards/useFlashcardOverview";
import { clampDailyGoal, DAILY_GOAL_DEFAULT, DAILY_GOAL_MAX, DAILY_GOAL_MIN, useDailyGoal } from "../src/hooks/useDailyGoal";
import { LANG_CODES } from "../src/services/deckStorage";
import { getMockDashboardStats } from "../src/mock/mockData";
import type { LanguageSummary, ReviewStreakData } from "../src/services/flashcardService";

const item = (code: string, over: Record<string, unknown> = {}) => ({
  code, learnable: code !== "vi", decks: 0, cards: 0, new: 0, due: 0, mastered: 0, weak: 0, ...over
});
const summaryOf = (over: Record<string, Record<string, unknown>> = {}): LanguageSummary => ({
  languages: LANG_CODES.map((c) => item(c, over[c])) as any,
  unconfirmed: { decks: [], cards: 0 }
});
const streakOf = (over: Partial<ReviewStreakData> = {}): ReviewStreakData => ({
  days: [], current_streak: 3, longest_streak: 5, today_reviews: 12, today_cards: 7, total_reviews: 100, ...over
});

describe("buildFlashcardOverview — gộp số liệu thật", () => {
  const base = { signedIn: true, summaryLoading: false, summaryError: false };

  it("cộng thẻ/đến hạn/đã thuộc, chọn ngôn ngữ nhiều thẻ đến hạn nhất", () => {
    const o = buildFlashcardOverview({
      ...base,
      summary: summaryOf({ en: { cards: 30, due: 4, mastered: 10, new: 5 }, de: { cards: 20, due: 9, mastered: 2, new: 8 }, ja: { cards: 5, due: 9, mastered: 1 } }),
      streak: streakOf()
    });
    expect(o).toMatchObject({ status: "ready", totalCards: 55, due: 22, mastered: 13, newCards: 13, reviewedToday: 7, streak: 3 });
    expect(o.topDueLang).toEqual({ code: "de", due: 9 }); // hoà (de, ja) -> ngôn ngữ đứng trước trong danh sách
    expect(o.topNewLang).toEqual({ code: "de", count: 8 });
  });

  it("không còn thẻ đến hạn -> all_done; chưa có thẻ nào -> empty", () => {
    expect(buildFlashcardOverview({ ...base, summary: summaryOf({ en: { cards: 3, mastered: 3 } }) }).status).toBe("all_done");
    expect(buildFlashcardOverview({ ...base, summary: summaryOf() }).status).toBe("empty");
  });

  it("chưa đăng nhập / đang tải / lỗi", () => {
    expect(buildFlashcardOverview({ ...base, signedIn: false }).status).toBe("guest");
    expect(buildFlashcardOverview({ ...base, summaryLoading: true }).status).toBe("loading");
    expect(buildFlashcardOverview({ ...base, summaryError: true }).status).toBe("error");
  });

  it("máy chủ cũ chưa có `mastered` hoặc `today_cards` thì trả null thay vì số sai", () => {
    const old = { languages: LANG_CODES.map((c) => ({ ...item(c), mastered: undefined })) as any, unconfirmed: { decks: [], cards: 0 } };
    old.languages[0].cards = 2;
    const o = buildFlashcardOverview({ ...base, summary: old, streak: streakOf({ today_cards: undefined }) });
    expect(o.mastered).toBeNull();
    expect(o.reviewedToday).toBeNull();
  });

  it("lỗi /stats/streak không làm hỏng phần còn lại", () => {
    const o = buildFlashcardOverview({ ...base, summary: summaryOf({ en: { cards: 2, due: 1 } }) });
    expect(o.status).toBe("ready");
    expect(o.reviewedToday).toBeNull();
    expect(o.streak).toBeNull();
  });
});

describe("useDailyGoal — mục tiêu ngày trong localStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    auth.user = { id: "user-1" };
  });

  it("mặc định 20, lưu và đọc lại theo từng tài khoản", () => {
    const { result, unmount } = renderHook(() => useDailyGoal());
    expect(result.current.goal).toBe(DAILY_GOAL_DEFAULT);
    act(() => result.current.setGoal(35));
    expect(result.current.goal).toBe(35);
    expect(window.localStorage.getItem("iuh_flashcard_daily_goal_user-1")).toBe("35");
    unmount();
    expect(renderHook(() => useDailyGoal()).result.current.goal).toBe(35);
    auth.user = { id: "user-2" };
    expect(renderHook(() => useDailyGoal()).result.current.goal).toBe(DAILY_GOAL_DEFAULT);
  });

  it("ép về khoảng cho phép và bỏ qua giá trị rác", () => {
    expect(clampDailyGoal(1)).toBe(DAILY_GOAL_MIN);
    expect(clampDailyGoal(99999)).toBe(DAILY_GOAL_MAX);
    expect(clampDailyGoal(12.6)).toBe(13);
    expect(clampDailyGoal("abc")).toBe(DAILY_GOAL_DEFAULT);
    window.localStorage.setItem("iuh_flashcard_daily_goal_user-1", "-5");
    expect(renderHook(() => useDailyGoal()).result.current.goal).toBe(DAILY_GOAL_MIN);
  });

  it("localStorage bị chặn thì vẫn đổi được trong phiên", () => {
    const get = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const set = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const { result } = renderHook(() => useDailyGoal());
    expect(result.current.goal).toBe(DAILY_GOAL_DEFAULT);
    act(() => result.current.setGoal(50));
    expect(result.current.goal).toBe(50);
    get.mockRestore();
    set.mockRestore();
  });
});

const Where: React.FC = () => <div data-testid="where">{useLocation().pathname}</div>;
const renderCard = () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <FlashcardDueCard />
        <Routes>
          <Route path="*" element={<Where />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};
const card = () => screen.getByTestId("flashcard-due-card");

describe("FlashcardDueCard — các trạng thái của thẻ Dashboard", () => {
  beforeEach(() => {
    window.localStorage.clear();
    auth.user = { id: "user-1" };
    svc.fetchLanguageSummary.mockReset();
    svc.fetchReviewStreak.mockReset();
    svc.fetchReviewStreak.mockResolvedValue({ ok: true, data: streakOf() });
  });

  it("đang tải: hiện skeleton có thông báo cho trình đọc màn hình", () => {
    svc.fetchLanguageSummary.mockReturnValue(new Promise(() => {}));
    renderCard();
    expect(card()).toHaveAttribute("data-status", "loading");
    expect(screen.getByRole("status")).toHaveTextContent(/Đang tải/);
  });

  it("có thẻ đến hạn: số thật, không còn 16/14/20 mẫu; nút dẫn tới ngôn ngữ nhiều thẻ đến hạn nhất", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ en: { cards: 30, due: 3, mastered: 10 }, ja: { cards: 12, due: 8, mastered: 4 } }) });
    renderCard();
    const start = await screen.findByRole("button", { name: /Bắt đầu Ôn tập Ngay/ });
    expect(start).toHaveTextContent("Tiếng Nhật");
    expect(start).toHaveTextContent("8 từ");
    expect(card()).toHaveTextContent("11 từ cần ôn");
    const stats = within(screen.getByTestId("flashcard-stats"));
    expect(stats.getByText("11")).toBeInTheDocument(); // cần ôn
    expect(stats.getByText("14")).toBeInTheDocument(); // đã thuộc 10 + 4
    expect(stats.getByText("42")).toBeInTheDocument(); // tổng thẻ
    expect(card()).toHaveTextContent("Đã ôn hôm nay: 7/20 từ");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "7");
    fireEvent.click(start);
    expect(screen.getByTestId("where")).toHaveTextContent("/flashcards/ja");
  });

  it("đổi mục tiêu ngày cập nhật thanh tiến độ và được nhớ lại", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ en: { cards: 5, due: 1 } }) });
    renderCard();
    const select = await screen.findByRole("combobox", { name: /Mục tiêu/ });
    fireEvent.change(select, { target: { value: "10" } });
    expect(card()).toHaveTextContent("Đã ôn hôm nay: 7/10 từ");
    expect(card()).toHaveTextContent("70%");
    expect(window.localStorage.getItem("iuh_flashcard_daily_goal_user-1")).toBe("10");
  });

  it("đạt mục tiêu thì báo hoàn thành", async () => {
    svc.fetchReviewStreak.mockResolvedValue({ ok: true, data: streakOf({ today_cards: 25 }) });
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ en: { cards: 5, due: 1 } }) });
    renderCard();
    expect(await screen.findByText(/đã đạt mục tiêu hôm nay/i)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "25");
  });

  it("hết thẻ đến hạn: hiện 'đã ôn xong' và gợi ý học từ mới nếu còn", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ de: { cards: 9, new: 6, mastered: 3 } }) });
    renderCard();
    expect(await screen.findByTestId("all-done")).toBeInTheDocument();
    expect(card()).toHaveTextContent("Đã ôn xong");
    expect(screen.queryByRole("button", { name: /Bắt đầu Ôn tập Ngay/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Học thêm từ mới/ }));
    expect(screen.getByTestId("where")).toHaveTextContent("/flashcards/de");
  });

  it("hết thẻ đến hạn và không còn từ mới: nút xem sổ thẻ", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ de: { cards: 9, mastered: 9 } }) });
    renderCard();
    fireEvent.click(await screen.findByRole("button", { name: /Xem sổ thẻ của tôi/ }));
    expect(screen.getByTestId("where")).toHaveTextContent("/flashcards");
  });

  it("chưa có thẻ nào: gợi ý tạo sổ", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf() });
    renderCard();
    expect(await screen.findByText("Bạn chưa có thẻ từ vựng nào")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Tạo sổ thẻ đầu tiên/ }));
    expect(screen.getByTestId("where")).toHaveTextContent("/flashcards");
  });

  it("lỗi API: hiện '—' và nút Thử lại, không ném lỗi", async () => {
    svc.fetchLanguageSummary.mockResolvedValueOnce({ ok: false, error: { message: "boom" } });
    renderCard();
    expect(await screen.findByRole("alert")).toHaveTextContent(/Không tải được số liệu Flashcard/);
    expect(within(screen.getByTestId("flashcard-stats")).getAllByText("—")).toHaveLength(3);
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ en: { cards: 2, due: 2 } }) });
    fireEvent.click(screen.getByRole("button", { name: /Thử lại/ }));
    await waitFor(() => expect(card()).toHaveAttribute("data-status", "ready"));
  });

  it("lỗi riêng /stats/streak: vẫn hiện số thẻ, ô đã ôn hôm nay là '—'", async () => {
    svc.fetchReviewStreak.mockResolvedValue({ ok: false, error: { message: "x" } });
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ en: { cards: 4, due: 4 } }) });
    renderCard();
    await screen.findByRole("button", { name: /Bắt đầu Ôn tập Ngay/ });
    expect(card()).toHaveTextContent("Đã ôn hôm nay: —/20 từ");
    expect(card()).toHaveTextContent("Chưa tải được số từ đã ôn hôm nay");
  });

  it("chưa đăng nhập: không gọi API, mời đăng nhập", () => {
    auth.user = null;
    renderCard();
    expect(card()).toHaveAttribute("data-status", "guest");
    expect(svc.fetchLanguageSummary).not.toHaveBeenCalled();
    expect(svc.fetchReviewStreak).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: /Đăng nhập/ }));
    expect(screen.getByTestId("where")).toHaveTextContent("/login");
  });
});

describe("PublicLearningProductivityCard — từ vựng đã học là số thật", () => {
  beforeEach(() => {
    auth.user = { id: "user-1" };
    svc.fetchLanguageSummary.mockReset();
    svc.fetchReviewStreak.mockReset();
    svc.fetchReviewStreak.mockResolvedValue({ ok: true, data: streakOf() });
  });
  const renderPublic = () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <PublicLearningProductivityCard stats={{ ...getMockDashboardStats(null), streakSource: "live", streakDays: 4 }} />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it("lấy số thẻ đã thuộc từ API, các ô chưa có nguồn thật có nhãn dữ liệu mẫu", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summaryOf({ en: { cards: 9, mastered: 6 }, fr: { cards: 3, mastered: 2 } }) });
    renderPublic();
    await waitFor(() => expect(screen.getByTestId("mastered-value")).toHaveTextContent("8"));
    expect(screen.getAllByTestId("sample-badge").length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText("248")).toBeNull(); // số mẫu cũ
  });

  it("lỗi API thì hiện '—' chứ không dùng số mẫu", async () => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: false, error: { message: "x" } });
    renderPublic();
    await waitFor(() => expect(screen.getByTestId("mastered-value")).toHaveTextContent("—"));
  });
});

describe("SampleDataBadge", () => {
  it("hiển thị nhãn", () => {
    render(<SampleDataBadge />);
    expect(screen.getByTestId("sample-badge")).toHaveTextContent("Dữ liệu mẫu");
  });
});
