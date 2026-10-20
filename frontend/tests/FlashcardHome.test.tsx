import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";

import { FlashcardHero, computeHeroTotals } from "../src/components/flashcards/FlashcardHero";
import { LanguageSelectionGrid, groupLanguages } from "../src/components/flashcards/LanguageSelectionGrid";
import { LANG_CODES } from "../src/services/deckStorage";
import type { LanguageSummary, ReviewStreakData } from "../src/services/flashcardService";

const item = (code: string, over: Record<string, unknown> = {}) => ({
  code, learnable: code !== "vi", decks: 0, cards: 0, new: 0, due: 0, weak: 0, ...over
});
const summaryOf = (over: Record<string, Record<string, unknown>> = {}): LanguageSummary => ({
  languages: LANG_CODES.map((c) => item(c, over[c])) as LanguageSummary["languages"],
  unconfirmed: { decks: [], cards: 0 }
});
const streak: ReviewStreakData = { days: [], current_streak: 6, longest_streak: 14, today_reviews: 22, total_reviews: 480 };

describe("computeHeroTotals", () => {
  it("cộng thẻ đến hạn, tổng từ, tổng sổ và chọn ngôn ngữ nhiều thẻ đến hạn nhất", () => {
    const t = computeHeroTotals(summaryOf({ en: { cards: 100, decks: 3, due: 18 }, de: { cards: 30, decks: 1, due: 25 }, ja: { cards: 5, decks: 1 } }));
    expect(t).toEqual({ due: 43, cards: 135, decks: 5, topDueLang: { code: "de", due: 25 } });
  });

  it("hoà số thẻ đến hạn thì lấy ngôn ngữ đứng trước; không có thẻ đến hạn thì không có gợi ý", () => {
    expect(computeHeroTotals(summaryOf({ en: { cards: 3, due: 4 }, de: { cards: 3, due: 4 } })).topDueLang?.code).toBe("en");
    expect(computeHeroTotals(summaryOf({ en: { cards: 3 } })).topDueLang).toBeNull();
    expect(computeHeroTotals(undefined)).toEqual({ due: 0, cards: 0, decks: 0, topDueLang: null });
  });
});

describe("FlashcardHero", () => {
  const renderHero = (props: Partial<React.ComponentProps<typeof FlashcardHero>> = {}) => {
    const onStudyLanguage = vi.fn();
    render(<FlashcardHero summary={summaryOf()} isLoading={false} isError={false} onStudyLanguage={onStudyLanguage} {...props} />);
    return { onStudyLanguage };
  };

  it("có tiêu đề h1 và 4 ô số liệu, kèm chuỗi ngày ôn từ nhật ký", () => {
    renderHero({ summary: summaryOf({ en: { cards: 10, decks: 2, due: 4 } }), streak });
    expect(screen.getByRole("heading", { level: 1, name: "Sổ Thẻ Từ Vựng" })).toBeInTheDocument();
    const stats = screen.getByTestId("hero-stats");
    expect(within(stats).getByText("Cần ôn hôm nay").previousSibling).toHaveTextContent("4");
    expect(within(stats).getByText("Tổng số từ").previousSibling).toHaveTextContent("10");
    expect(within(stats).getByText("Chuỗi ngày ôn").previousSibling).toHaveTextContent("6");
    expect(stats).toHaveTextContent("Hôm nay đã ôn 22 lượt");
  });

  it("có thẻ đến hạn: nút Ôn ngay dẫn tới ngôn ngữ nhiều thẻ đến hạn nhất", () => {
    const { onStudyLanguage } = renderHero({ summary: summaryOf({ en: { cards: 10, due: 4 }, de: { cards: 9, due: 7 } }) });
    fireEvent.click(screen.getByRole("button", { name: /Ôn Tiếng Đức · 7 từ/ }));
    expect(onStudyLanguage).toHaveBeenCalledWith("de");
  });

  it("đã ôn xong thì không có nút, hiện lời chúc; chưa có từ thì mời chọn ngôn ngữ", () => {
    const { unmount } = render(<FlashcardHero summary={summaryOf({ en: { cards: 10 } })} isLoading={false} isError={false} onStudyLanguage={vi.fn()} />);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText(/đã ôn xong/)).toBeInTheDocument();
    unmount();
    renderHero();
    expect(screen.getByText(/Chọn một ngôn ngữ bên dưới/)).toBeInTheDocument();
  });

  it("lỗi tải hoặc không có streak thì hiện dấu —, không báo lỗi chặn màn hình", () => {
    renderHero({ summary: undefined, isError: true });
    const stats = screen.getByTestId("hero-stats");
    expect(within(stats).getByText("Cần ôn hôm nay").previousSibling).toHaveTextContent("—");
    expect(within(stats).getByText("Chuỗi ngày ôn").previousSibling).toHaveTextContent("—");
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("groupLanguages / LanguageSelectionGrid chia nhóm", () => {
  it("đang học xếp theo số thẻ đến hạn rồi số từ; ngôn ngữ chưa có từ nằm ở nhóm khám phá", () => {
    const items = summaryOf({ en: { cards: 50, due: 2 }, de: { cards: 10, due: 9 }, ja: { cards: 80 } }).languages;
    const { learning, discover } = groupLanguages(items);
    expect(learning.map((i) => i.code)).toEqual(["de", "en", "ja"]);
    expect(discover.map((i) => i.code)).toEqual(["zh", "ko", "fr", "es", "ru", "th", "vi"]);
  });

  const renderGrid = (summary?: LanguageSummary) =>
    render(<LanguageSelectionGrid summary={summary} isLoading={false} isError={false} onRetry={vi.fn()} onSelect={vi.fn()} />);

  it("có ngôn ngữ đang học thì hiện 2 nhóm 'Đang học' và 'Khám phá thêm', vẫn đủ 10 nút", () => {
    renderGrid(summaryOf({ de: { cards: 12, decks: 1, new: 3 } }));
    expect(screen.getByRole("heading", { name: /Đang học/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Khám phá thêm" })).toBeInTheDocument();
    expect(within(screen.getByTestId("language-grid")).getAllByRole("button")).toHaveLength(10);
    expect(within(screen.getByRole("list", { name: "Ngôn ngữ đang học" })).getAllByRole("button")).toHaveLength(1);
    // Đã học = (12 - 3) / 12 = 75%
    expect(screen.getByRole("progressbar", { name: "Đã học 75%" })).toHaveAttribute("aria-valuenow", "75");
  });

  it("chưa có từ nào (hoặc chưa tải xong) thì chỉ một lưới, không chia nhóm", () => {
    const { unmount } = renderGrid(summaryOf());
    expect(screen.queryByRole("heading", { name: "Khám phá thêm" })).toBeNull();
    unmount();
    renderGrid(undefined);
    expect(screen.queryByRole("heading", { name: /Đang học/ })).toBeNull();
    expect(screen.getAllByTestId(/^lang-card-/)).toHaveLength(10);
  });
});
