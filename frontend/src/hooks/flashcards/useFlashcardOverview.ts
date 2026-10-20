import { useAuth } from "../useAuth";
import type { LanguageSummary, ReviewStreakData } from "../../services/flashcardService";
import { computeHeroTotals } from "../../components/flashcards/FlashcardHero";
import { useLanguageSummary } from "./useLanguageCollections";
import { useReviewStreak } from "./useReviewStreak";

/**
 * - guest: chưa đăng nhập, không gọi API.
 * - loading / error: chưa có dữ liệu (error không chặn Dashboard, giao diện hiện "—").
 * - empty: đã đăng nhập nhưng chưa có thẻ nào trong 10 bộ sưu tập ngôn ngữ.
 * - all_done: có thẻ nhưng không còn thẻ nào đến hạn.
 * - ready: có thẻ đến hạn.
 */
export type FlashcardOverviewStatus = "guest" | "loading" | "error" | "empty" | "all_done" | "ready";

export interface FlashcardOverview {
  status: FlashcardOverviewStatus;
  totalCards: number;
  /** Tổng số thẻ đến hạn ôn của mọi ngôn ngữ. */
  due: number;
  /** Thẻ chưa học lần nào. */
  newCards: number;
  /** Tổng số thẻ đã thuộc; null nếu máy chủ chưa trả số liệu này. */
  mastered: number | null;
  /** Ngôn ngữ có nhiều thẻ đến hạn nhất (hoà thì lấy ngôn ngữ đứng trước). */
  topDueLang: { code: string; due: number } | null;
  /** Ngôn ngữ có nhiều thẻ mới nhất, dùng khi hết thẻ đến hạn nhưng còn từ chưa học. */
  topNewLang: { code: string; count: number } | null;
  /** Số thẻ khác nhau đã ôn hôm nay; null nếu không tải được. */
  reviewedToday: number | null;
  /** Chuỗi ngày ôn liên tiếp; null nếu không tải được. */
  streak: number | null;
}

interface OverviewInput {
  signedIn: boolean;
  summary?: LanguageSummary;
  summaryLoading: boolean;
  summaryError: boolean;
  streak?: ReviewStreakData;
}

/** Hàm thuần gộp số liệu của 10 ngôn ngữ + nhật ký ôn tập thành số liệu cho Dashboard. */
export function buildFlashcardOverview({ signedIn, summary, summaryLoading, summaryError, streak }: OverviewInput): FlashcardOverview {
  const languages = summary?.languages ?? [];
  const totals = computeHeroTotals(summary);
  const newCards = languages.reduce((sum, l) => sum + l.new, 0);

  let topNewLang: FlashcardOverview["topNewLang"] = null;
  for (const l of languages) {
    if (l.new > 0 && (!topNewLang || l.new > topNewLang.count)) topNewLang = { code: l.code, count: l.new };
  }

  // Chỉ cộng khi MỌI ngôn ngữ đều có trường mastered; máy chủ cũ thiếu trường thì hiện "—" thay vì số sai.
  const hasMastered = languages.length > 0 && languages.every((l) => typeof l.mastered === "number");
  const mastered = hasMastered ? languages.reduce((sum, l) => sum + (l.mastered ?? 0), 0) : null;

  let status: FlashcardOverviewStatus;
  if (!signedIn) status = "guest";
  else if (!summary) status = summaryLoading && !summaryError ? "loading" : "error";
  else if (totals.cards === 0) status = "empty";
  else status = totals.due > 0 ? "ready" : "all_done";

  return {
    status,
    totalCards: totals.cards,
    due: totals.due,
    newCards,
    mastered,
    topDueLang: totals.topDueLang,
    topNewLang,
    reviewedToday: typeof streak?.today_cards === "number" ? streak.today_cards : null,
    streak: streak ? streak.current_streak : null
  };
}

/**
 * Số liệu Flashcard THẬT cho Dashboard, lấy từ GET /languages và GET /stats/streak (cùng cache với trang Flashcard).
 * Mỗi nguồn lỗi độc lập: lỗi /languages -> status "error"; lỗi /stats/streak -> chỉ các ô đã ôn hôm nay và chuỗi ngày hiện "—".
 */
export function useFlashcardOverview(): FlashcardOverview & { refetch: () => void } {
  const { user } = useAuth();
  const signedIn = !!user;
  const languages = useLanguageSummary({ enabled: signedIn });
  const review = useReviewStreak({ enabled: signedIn, staleTime: 0 });

  const overview = buildFlashcardOverview({
    signedIn,
    summary: languages.summary,
    summaryLoading: languages.isLoading,
    summaryError: languages.isError,
    streak: review.streak
  });
  return {
    ...overview,
    refetch: () => {
      void languages.refetch();
      void review.refetch();
    }
  };
}
