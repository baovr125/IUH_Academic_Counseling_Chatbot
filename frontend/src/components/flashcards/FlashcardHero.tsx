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

/** Banner đầu trang Flashcard: cùng ngôn ngữ thiết kế với banner Dashboard (gradient navy, kính mờ, điểm nhấn cam). */
export const FlashcardHero: React.FC<FlashcardHeroProps> = ({ summary, isLoading, isError, streak, onStudyLanguage }) => {
  const totals = computeHeroTotals(summary);
  const waiting = isLoading && !summary;
  const value = (n: number) =>
    waiting ? <span aria-hidden="true" className="block h-6 w-10 animate-pulse rounded-lg bg-white/30 motion-reduce:animate-none" /> : isError && !summary ? "—" : n;
  const top = totals.topDueLang;

  let message: React.ReactNode;
  if (waiting) {
    message = "Đang tải số liệu học tập của bạn…";
  } else if (top) {
    message = (
      <>
        Bạn có <strong className="font-bold text-white">{totals.due} từ</strong> đến hạn ôn hôm nay. Ôn đều mỗi ngày để nhớ lâu hơn.
      </>
    );
  } else if (totals.cards > 0) {
    message = (
      <span className="inline-flex items-center gap-1.5">
        <PartyPopper size={16} className="text-orange-300" aria-hidden="true" /> Hôm nay bạn đã ôn xong, hãy quay lại vào ngày mai.
      </span>
    );
  } else {
    message = "Chọn một ngôn ngữ bên dưới để bắt đầu xây dựng bộ từ vựng của bạn.";
  }

  return (
    <section
      aria-label="Tổng quan học tập"
      className="relative mb-8 overflow-hidden rounded-3xl bg-gradient-to-r from-[#152a6e] via-[#1e3a8a] to-[#2563eb] p-6 text-white shadow-xl shadow-blue-950/15 sm:p-8"
    >
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-blue-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 right-1/3 h-48 w-48 rounded-full bg-orange-500/15 blur-2xl" />

      <div className="relative z-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] lg:items-center">
        <div className="space-y-3">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur-md">
            <BookOpen size={14} className="text-orange-400" aria-hidden="true" />
            Spaced Repetition · FSRS
          </span>
          <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">Sổ Thẻ Từ Vựng</h1>
          <p className="max-w-xl text-sm leading-relaxed text-blue-100/90 sm:text-base">
            Học từ vựng theo từng ngôn ngữ với lặp lại ngắt quãng, phát âm chuẩn và câu ngữ cảnh.
          </p>
          <p className="text-sm text-blue-100">{message}</p>

          {top && (
            <button
              type="button"
              onClick={() => onStudyLanguage(top.code)}
              className="group inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-orange-700 to-amber-700 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-orange-500/25 transition-all hover:scale-[1.02] hover:from-orange-800 hover:to-amber-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-blue-900"
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
          <FcStat variant="onDark" label="Cần ôn hôm nay" value={value(totals.due)} icon={<Target size={20} />} />
          <FcStat variant="onDark" label="Tổng số từ" value={value(totals.cards)} icon={<BookOpen size={20} />} />
          <FcStat variant="onDark" label="Số sổ thẻ" value={value(totals.decks)} icon={<Layers size={20} />} />
          <FcStat
            variant="onDark"
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
