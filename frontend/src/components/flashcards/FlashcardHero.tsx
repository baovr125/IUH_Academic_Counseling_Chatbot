import React from "react";
import { ArrowRight, BookOpen, Flame, Layers, PartyPopper, Target } from "lucide-react";
import { LANG_CONFIG } from "../../services/deckStorage";
import type { LanguageSummary, ReviewStreakData } from "../../services/flashcardService";
import { FcStat, LangFlag } from "./ui";

export interface HeroTotals {
  due: number;
  cards: number;
  decks: number;
  /** Ngôn ngữ có nhiều thẻ đến hạn nhất (hoà thì lấy ngôn ngữ đứng trước trong danh sách). */
  topDueLang: { code: string; due: number } | null;
}

/** Cộng số liệu của các ngôn ngữ. Hàm thuần để dễ kiểm thử. */
export function computeHeroTotals(summary?: LanguageSummary): HeroTotals {
  const totals: HeroTotals = { due: 0, cards: 0, decks: 0, topDueLang: null };
  for (const l of summary?.languages ?? []) {
    totals.due += l.due;
    totals.cards += l.cards;
    totals.decks += l.decks;
    if (l.due > 0 && (!totals.topDueLang || l.due > totals.topDueLang.due)) {
      totals.topDueLang = { code: l.code, due: l.due };
    }
  }
  return totals;
}

interface FlashcardHeroProps {
  summary?: LanguageSummary;
  isLoading: boolean;
  isError: boolean;
  streak?: ReviewStreakData;
  onStudyLanguage: (langCode: string) => void;
}

/** Banner đầu trang Flashcard: cùng ngôn ngữ thiết kế với banner Dashboard (nền sáng xanh nhạt, thẻ trắng, màu chủ đạo brand; cam chỉ cho tín hiệu cần ôn/streak). */
export const FlashcardHero: React.FC<FlashcardHeroProps> = ({ summary, isLoading, isError, streak, onStudyLanguage }) => {
  const totals = computeHeroTotals(summary);
  const waiting = isLoading && !summary;
  const value = (n: number) =>
    waiting ? <span aria-hidden="true" className="block h-6 w-10 animate-pulse rounded-lg bg-brand-100 motion-reduce:animate-none dark:bg-slate-600" /> : isError && !summary ? "—" : n;
  const top = totals.topDueLang;

  let message: React.ReactNode;
  if (waiting) {
    message = "Đang tải số liệu học tập của bạn…";
  } else if (top) {
    message = (
      <>
        Bạn có <strong className="font-bold text-brand-900 dark:text-white">{totals.due} từ</strong> đến hạn ôn hôm nay. Ôn đều mỗi ngày để nhớ lâu hơn.
      </>
    );
  } else if (totals.cards > 0) {
    message = (
      <span className="inline-flex items-center gap-1.5">
        <PartyPopper size={16} className="text-brand-500 dark:text-brand-300" aria-hidden="true" /> Hôm nay bạn đã ôn xong, hãy quay lại vào ngày mai.
      </span>
    );
  } else {
    message = "Chọn một ngôn ngữ bên dưới để bắt đầu xây dựng bộ từ vựng của bạn.";
  }

  return (
    <section
      aria-label="Tổng quan học tập"
      className="relative mb-8 overflow-hidden rounded-3xl border border-brand-100 bg-gradient-to-r from-brand-50 via-white to-sky-50 p-6 text-slate-800 shadow-sm dark:border-slate-700 dark:from-slate-800 dark:via-slate-800 dark:to-brand-950/60 dark:text-white sm:p-8"
    >
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-200/40 blur-3xl dark:bg-brand-400/20" />
      <div className="pointer-events-none absolute -bottom-16 right-1/3 h-48 w-48 rounded-full bg-sky-200/40 blur-2xl dark:bg-sky-500/10" />

      <div className="relative z-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] lg:items-center">
        <div className="space-y-3">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-semibold text-brand-700 ring-1 ring-brand-100 dark:bg-white/10 dark:text-white dark:ring-0">
            <BookOpen size={14} className="text-brand-600 dark:text-brand-300" aria-hidden="true" />
            Spaced Repetition · FSRS
          </span>
          <h1 className="text-2xl font-extrabold tracking-tight text-brand-900 dark:text-white sm:text-3xl">Sổ Thẻ Từ Vựng</h1>
          <p className="max-w-xl text-sm leading-relaxed text-slate-600 dark:text-brand-100/90 sm:text-base">
            Học từ vựng theo từng ngôn ngữ với lặp lại ngắt quãng, phát âm chuẩn và câu ngữ cảnh.
          </p>
          <p className="text-sm text-slate-700 dark:text-brand-100">{message}</p>

          {top && (
            <button
              type="button"
              onClick={() => onStudyLanguage(top.code)}
              className="group inline-flex items-center gap-2.5 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-brand-600/25 transition-all hover:scale-[1.02] hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-800"
            >
              <LangFlag lang={top.code} size="sm" />
              <span>
                Ôn {LANG_CONFIG[top.code]?.viName ?? top.code} · {top.due} từ
              </span>
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3" data-testid="hero-stats">
          <FcStat tone="orange" label="Cần ôn hôm nay" value={value(totals.due)} icon={<Target size={20} />} />
          <FcStat tone="blue" label="Tổng số từ" value={value(totals.cards)} icon={<BookOpen size={20} />} />
          <FcStat tone="sky" label="Số sổ thẻ" value={value(totals.decks)} icon={<Layers size={20} />} />
          <FcStat
            tone="orange"
            label="Chuỗi ngày ôn"
            value={streak ? streak.current_streak : "—"}
            icon={<Flame size={20} />}
            hint={streak ? `Hôm nay đã ôn ${streak.today_reviews} lượt` : undefined}
          />
        </div>
      </div>
    </section>
  );
};
