import React, { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Folder, Languages, Search, Volume2 } from "lucide-react";
import { LANG_CONFIG } from "../../services/deckStorage";
import type { LanguageCardItem, LanguageCardSort, LanguageCardStatus, LanguageSummaryItem } from "../../services/flashcardService";
import { useLanguageCards } from "../../hooks/flashcards/useLanguageCollections";
import { FcBadge, FcButton, FcCard, FcEmpty, FcLoading, FcPage, FcSkeleton, FcTabs, LangFlag } from "./ui";

export type LibraryTab = "decks" | "words";

interface LanguageLibraryProps {
  lang: string;
  tab: LibraryTab;
  onTabChange: (tab: LibraryTab) => void;
  onBack: () => void;
  stats?: LanguageSummaryItem;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onOpenTranslation: () => void;
  /** Nội dung tab "Sổ thẻ" (DeckDashboard của ngôn ngữ này). */
  children: React.ReactNode;
}

const PAGE_SIZE = 20;

const SORTS: { value: LanguageCardSort; label: string }[] = [
  { value: "recent", label: "Mới thêm" },
  { value: "alpha", label: "A → Z" },
  { value: "due", label: "Sắp đến hạn ôn" }
];

const STATUSES: { value: LanguageCardStatus; label: string }[] = [
  { value: "all", label: "Tất cả" },
  { value: "new", label: "Mới" },
  { value: "due", label: "Cần ôn" },
  { value: "weak", label: "Hay quên" }
];

const FIELD =
  "rounded-xl border border-slate-200 bg-white text-sm text-slate-800 focus:border-blue-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 " +
  "dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500";

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

const WordRow: React.FC<{ card: LanguageCardItem; lang: string; onPlayAudio: LanguageLibraryProps["onPlayAudio"] }> = ({ card, lang, onPlayAudio }) => (
  <FcCard as="li" padding="sm">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h4 className="text-base font-bold text-slate-800 dark:text-slate-100" lang={lang}>{card.term}</h4>
        {card.phonetic && <p className="font-mono text-xs text-blue-600 dark:text-blue-300">{card.phonetic}</p>}
        <p className="mt-1 text-sm font-medium text-slate-600 dark:text-slate-300">{card.definition}</p>
        {(card.example_sentence || card.example) && (
          <p className="mt-2 rounded-xl border border-slate-100 bg-slate-50 p-2.5 text-xs italic text-slate-500 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-400" lang={lang}>
            “{card.example_sentence || card.example}”
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onPlayAudio(card.audio_url, card.term, lang, card.phonetic)}
        className="shrink-0 rounded-full p-2 text-blue-600 transition-colors hover:bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-blue-300 dark:hover:bg-slate-700"
        aria-label={`Nghe phát âm ${card.term}`}
      >
        <Volume2 size={16} aria-hidden="true" />
      </button>
    </div>
    <div className="mt-3 flex flex-wrap items-center gap-2">
      {card.deck_title && (
        <FcBadge tone="slate" icon={<Folder size={12} aria-hidden="true" />}>
          {card.deck_title}
        </FcBadge>
      )}
      {(card.part_of_speech || card.partOfSpeech) && (
        <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">{card.part_of_speech || card.partOfSpeech}</span>
      )}
      {card.state === 0 && <FcBadge tone="sky">Mới</FcBadge>}
      {(card.lapses ?? 0) > 0 && <FcBadge tone="rose">Hay quên</FcBadge>}
    </div>
  </FcCard>
);

const WordsTab: React.FC<Pick<LanguageLibraryProps, "lang" | "onPlayAudio" | "onOpenTranslation">> = ({ lang, onPlayAudio, onOpenTranslation }) => {
  const meta = LANG_CONFIG[lang];
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<LanguageCardSort>("recent");
  const [status, setStatus] = useState<LanguageCardStatus>("all");
  const [offset, setOffset] = useState(0);
  const q = useDebounced(search.trim(), 300);

  // Đổi bộ lọc thì quay về trang đầu.
  useEffect(() => setOffset(0), [q, sort, status, lang]);

  const { page, isLoading, isFetching, isError, errorMessage, refetch } = useLanguageCards(lang, {
    q: q || undefined,
    sort,
    status,
    limit: PAGE_SIZE,
    offset
  });
  const items = page?.items ?? [];
  const total = page?.total ?? 0;
  const filtering = !!q || status !== "all";

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 dark:text-slate-400" aria-hidden="true" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            maxLength={60}
            placeholder={`Tìm từ ${meta.viName} hoặc nghĩa tiếng Việt…`}
            aria-label="Tìm từ vựng"
            className={`${FIELD} w-full py-2.5 pl-10 pr-4`}
          />
        </div>
        <select value={sort} onChange={(e) => setSort(e.target.value as LanguageCardSort)} aria-label="Sắp xếp" className={`${FIELD} px-3.5 py-2.5 font-semibold`}>
          {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Lọc theo trạng thái">
        {STATUSES.map((s) => (
          <button
            key={s.value}
            type="button"
            aria-pressed={status === s.value}
            onClick={() => setStatus(s.value)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-bold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
              status === s.value
                ? "bg-blue-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <FcLoading label="Đang tải từ vựng" className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {[0, 1, 2, 3].map((n) => (
            <FcCard key={n} padding="sm" className="space-y-3">
              <FcSkeleton className="h-5 w-1/3" />
              <FcSkeleton className="h-4 w-2/3" />
              <FcSkeleton className="h-10 w-full" />
            </FcCard>
          ))}
        </FcLoading>
      ) : isError ? (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-sm font-semibold text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
          {errorMessage || "Không tải được danh sách từ vựng."}
          <div className="mt-3">
            <FcButton variant="secondary" size="sm" onClick={() => void refetch()}>Thử lại</FcButton>
          </div>
        </div>
      ) : items.length === 0 ? (
        <FcEmpty
          data-testid="words-empty"
          icon={<LangFlag lang={lang} size="lg" />}
          title={filtering ? "Không tìm thấy từ nào" : `Chưa có từ vựng ${meta.viName} nào`}
          description={filtering ? "Thử đổi từ khóa hoặc bộ lọc." : `Dịch một từ ${meta.viName} sang tiếng Việt rồi bấm “Lưu Flashcard”, từ sẽ tự vào bộ sưu tập này.`}
        >
          {!filtering && (
            <FcButton variant="primary" onClick={onOpenTranslation} icon={<Languages size={16} />}>
              Mở Dịch thuật
            </FcButton>
          )}
        </FcEmpty>
      ) : (
        <>
          <ul className={`grid grid-cols-1 gap-3 transition-opacity lg:grid-cols-2 ${isFetching ? "opacity-70" : ""}`} data-testid="words-list">
            {items.map((card) => <WordRow key={card.id} card={card} lang={lang} onPlayAudio={onPlayAudio} />)}
          </ul>
          <div className="mt-4 flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
            <span>Hiển thị {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} / {total} từ</span>
            <div className="flex gap-2">
              <FcButton variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} aria-label="Trang trước" className="!px-2.5">
                <ChevronLeft size={16} aria-hidden="true" />
              </FcButton>
              <FcButton variant="secondary" size="sm" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)} aria-label="Trang sau" className="!px-2.5">
                <ChevronRight size={16} aria-hidden="true" />
              </FcButton>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export const LanguageLibrary: React.FC<LanguageLibraryProps> = ({ lang, tab, onTabChange, onBack, stats, onPlayAudio, onOpenTranslation, children }) => {
  const meta = LANG_CONFIG[lang];
  return (
    <FcPage width="lg">
      <nav aria-label="Đường dẫn" className="mb-4 flex items-center gap-1.5 text-sm">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 rounded-lg px-1.5 py-1 font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-blue-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-blue-300"
        >
          <ChevronLeft size={16} aria-hidden="true" />
          Tất cả ngôn ngữ
        </button>
        <ChevronRight size={14} className="text-slate-300 dark:text-slate-600" aria-hidden="true" />
        <span aria-current="page" className="font-bold text-slate-800 dark:text-slate-100">{meta.viName}</span>
      </nav>

      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <LangFlag lang={lang} size="xl" />
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">{meta.viName}</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400" lang={lang}>{meta.nativeName}</p>
          </div>
        </div>
        {stats && (
          <ul className="flex flex-wrap items-center gap-2" aria-label="Thống kê ngôn ngữ">
            <li><FcBadge tone="blue">{stats.cards} từ</FcBadge></li>
            <li><FcBadge tone="slate">{stats.decks} sổ</FcBadge></li>
            {stats.due > 0 && <li><FcBadge tone="orange">{stats.due} cần ôn</FcBadge></li>}
            {stats.weak > 0 && <li><FcBadge tone="rose">{stats.weak} hay quên</FcBadge></li>}
          </ul>
        )}
      </header>

      <FcTabs
        ariaLabel="Nội dung bộ sưu tập"
        value={tab}
        onChange={onTabChange}
        tabs={[
          { value: "decks", label: "Sổ thẻ" },
          { value: "words", label: "Tất cả từ vựng" }
        ]}
        className="mb-6"
      />

      {tab === "decks" ? children : <WordsTab lang={lang} onPlayAudio={onPlayAudio} onOpenTranslation={onOpenTranslation} />}
    </FcPage>
  );
};
