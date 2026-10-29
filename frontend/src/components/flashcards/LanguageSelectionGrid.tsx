import React from "react";
import { AlertTriangle, Lock, RefreshCw } from "lucide-react";
import { LANG_CODES, LANG_CONFIG } from "../../services/deckStorage";
import type { LanguageSummary, LanguageSummaryItem } from "../../services/flashcardService";
import { FcBadge, FcButton, FcCard, FcSkeleton, LangFlag } from "./ui";

interface LanguageSelectionGridProps {
  /** undefined khi đang tải hoặc lỗi: lưới vẫn hiển thị đủ 10 ngôn ngữ để người dùng không bị chặn. */
  summary?: LanguageSummary;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string | null;
  onRetry: () => void;
  onSelect: (langCode: string) => void;
}

const EMPTY_ITEM = (code: string): LanguageSummaryItem => ({
  code, learnable: LANG_CONFIG[code].learnable, decks: 0, cards: 0, new: 0, due: 0, weak: 0
});

/** Tách "đang học" (đã có từ) và "khám phá thêm". Đang học xếp theo số thẻ đến hạn rồi số từ, còn lại giữ thứ tự chuẩn. */
export function groupLanguages(items: LanguageSummaryItem[]): { learning: LanguageSummaryItem[]; discover: LanguageSummaryItem[] } {
  const learning = items
    .filter((i) => i.cards > 0)
    .sort((a, b) => b.due - a.due || b.cards - a.cards || LANG_CODES.indexOf(a.code) - LANG_CODES.indexOf(b.code));
  const discover = items.filter((i) => i.cards === 0);
  return { learning, discover };
}

const LanguageCard: React.FC<{
  item: LanguageSummaryItem;
  isLoading: boolean;
  hasSummary: boolean;
  onSelect: (langCode: string) => void;
}> = ({ item, isLoading, hasSummary, onSelect }) => {
  const meta = LANG_CONFIG[item.code];
  // Tiếng Việt là ngôn ngữ giải nghĩa: khóa, trừ khi còn sổ cũ mang mã 'vi'.
  const locked = !meta.learnable && item.decks === 0;
  const learnedPct = item.cards > 0 ? Math.round(((item.cards - item.new) / item.cards) * 100) : 0;

  return (
    <FcCard as="li" padding="none" interactive={!locked} className={locked ? "opacity-70" : ""}>
      <button
        type="button"
        data-testid={`lang-card-${item.code}`}
        aria-label={`${meta.viName}${locked ? " (đã khóa)" : ""}`}
        aria-disabled={locked}
        onClick={() => !locked && onSelect(item.code)}
        className={`group flex h-full w-full flex-col rounded-3xl p-4 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 sm:p-5 ${
          locked ? "cursor-not-allowed" : ""
        }`}
      >
        <span className="flex w-full items-start justify-between gap-2">
          <LangFlag lang={item.code} size="lg" className={locked ? "opacity-60 grayscale" : ""} />
          {!locked && item.due > 0 && <FcBadge tone="orange">{item.due} cần ôn</FcBadge>}
        </span>

        <span className="mt-4 text-base font-bold text-slate-800 transition-colors group-hover:text-brand-600 dark:text-slate-100 dark:group-hover:text-brand-300">
          {meta.viName}
        </span>
        {meta.nativeName !== meta.viName && (
          <span className="text-xs text-slate-500 dark:text-slate-400" lang={item.code}>
            {meta.nativeName}
          </span>
        )}

        {locked ? (
          <span className="mt-3 flex items-start gap-1 text-xs leading-snug text-slate-500 dark:text-slate-400">
            <Lock size={12} className="mt-0.5 shrink-0" aria-hidden="true" />
            Là ngôn ngữ giải nghĩa, nên không có bộ sưu tập riêng
          </span>
        ) : isLoading && !hasSummary ? (
          <span className="mt-3 block w-full">
            <FcSkeleton className="h-3.5 w-24" />
          </span>
        ) : item.cards === 0 ? (
          <span className="mt-3 text-xs font-medium text-slate-500 dark:text-slate-400">Chưa có từ vựng</span>
        ) : (
          <span className="mt-3 flex w-full flex-col gap-1.5">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
              {item.cards} từ • {item.decks} sổ
            </span>
            <span
              role="progressbar"
              aria-label={`Đã học ${learnedPct}%`}
              aria-valuenow={learnedPct}
              aria-valuemin={0}
              aria-valuemax={100}
              className="block h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700"
            >
              <span className="block h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${learnedPct}%` }} />
            </span>
            <span className="text-xs sm:text-[11px] font-medium text-slate-500 dark:text-slate-400">Đã học {learnedPct}%</span>
          </span>
        )}
      </button>
    </FcCard>
  );
};

export const LanguageSelectionGrid: React.FC<LanguageSelectionGridProps> = ({
  summary,
  isLoading,
  isError,
  errorMessage,
  onRetry,
  onSelect
}) => {
  const byCode = new Map((summary?.languages ?? []).map((l) => [l.code, l]));
  const items = LANG_CODES.map((code) => byCode.get(code) ?? EMPTY_ITEM(code));
  const { learning, discover } = groupLanguages(items);
  // Chỉ chia nhóm khi đã biết số liệu và có ít nhất một ngôn ngữ đang học; ngược lại hiện một lưới duy nhất.
  const grouped = !!summary && learning.length > 0;

  const renderList = (list: LanguageSummaryItem[], label: string) => (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-5" aria-label={label}>
      {list.map((item) => (
        <LanguageCard key={item.code} item={item} isLoading={isLoading} hasSummary={!!summary} onSelect={onSelect} />
      ))}
    </ul>
  );

  return (
    <section aria-labelledby="flashcard-language-heading">
      <div className="mb-5">
        <h2 id="flashcard-language-heading" className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
          Chọn ngôn ngữ để học
        </h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Mỗi ngôn ngữ có bộ sưu tập từ vựng riêng. Từ bạn lưu từ Dịch thuật sẽ tự vào đúng ngôn ngữ.
        </p>
      </div>

      {isError && (
        <div
          role="alert"
          className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-red-200 bg-red-50 p-3.5 text-xs font-semibold text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300"
        >
          <span className="flex items-center gap-2">
            <AlertTriangle size={16} aria-hidden="true" />
            {errorMessage || "Không tải được số liệu các ngôn ngữ."} Bạn vẫn có thể chọn ngôn ngữ bên dưới.
          </span>
          <FcButton variant="secondary" size="sm" onClick={onRetry} icon={<RefreshCw size={13} />}>
            Thử lại
          </FcButton>
        </div>
      )}

      <div data-testid="language-grid" className="space-y-8">
        {grouped ? (
          <>
            <div>
              <h3 className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Đang học <FcBadge tone="blue">{learning.length}</FcBadge>
              </h3>
              {renderList(learning, "Ngôn ngữ đang học")}
            </div>
            {discover.length > 0 && (
              <div>
                <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Khám phá thêm</h3>
                {renderList(discover, "Ngôn ngữ khám phá thêm")}
              </div>
            )}
          </>
        ) : (
          renderList(items, "Các ngôn ngữ")
        )}
      </div>
    </section>
  );
};
