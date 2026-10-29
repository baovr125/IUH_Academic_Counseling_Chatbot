import React, { useState, useMemo } from "react";
import { Virtuoso } from "react-virtuoso";
import { BookOpen, FileSpreadsheet, Pencil, Plus, Search, Trash2, Volume2 } from "lucide-react";
import type { BackendCardItem, BackendDeck } from "../../services/flashcardService";
import { FcBadge, FcButton, FcCard, FcEmpty, FcLoading, FcSkeleton } from "./ui";

interface CardListViewProps {
  deck: BackendDeck;
  cards: BackendCardItem[];
  isLoading: boolean;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onOpenEditCard: (card: BackendCardItem) => void;
  /** Yêu cầu xóa thẻ; việc xác nhận do nơi gọi đảm nhiệm (hộp thoại trong ứng dụng). */
  onDeleteCard: (cardId: string) => void | Promise<void>;
  onOpenAddCard: () => void;
  onOpenImportExcel?: () => void;
}

const ICON_BTN =
  "rounded-full p-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500";

export const CardListView: React.FC<CardListViewProps> = ({
  deck,
  cards,
  isLoading,
  onPlayAudio,
  onOpenEditCard,
  onDeleteCard,
  onOpenAddCard,
  onOpenImportExcel
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const deckLang = deck.lang_code || deck.langCode || "en";

  const filteredCards = useMemo(() => {
    if (!searchTerm.trim()) return cards;
    const query = searchTerm.toLowerCase().trim();
    return cards.filter(
      (c) =>
        c.term.toLowerCase().includes(query) ||
        c.definition.toLowerCase().includes(query) ||
        (c.phonetic && c.phonetic.toLowerCase().includes(query)) ||
        (c.example_sentence && c.example_sentence.toLowerCase().includes(query))
    );
  }, [cards, searchTerm]);

  if (isLoading) {
    return (
      <FcLoading label="Đang tải danh sách thẻ" className="flex flex-col gap-3">
        {[0, 1, 2, 3].map((n) => (
          <FcCard key={n} padding="sm" className="space-y-3">
            <FcSkeleton className="h-4 w-16" />
            <FcSkeleton className="h-5 w-1/3" />
            <FcSkeleton className="h-4 w-2/3" />
          </FcCard>
        ))}
      </FcLoading>
    );
  }

  if (cards.length === 0) {
    return (
      <FcEmpty
        icon={<BookOpen size={30} />}
        title="Chưa có thẻ từ vựng nào trong danh sách"
        description='Bấm nút "Thêm từ vựng" ở trên hoặc nhập từ Excel để tạo danh sách từ vựng cho sổ này.'
      >
        <FcButton variant="primary" onClick={onOpenAddCard} icon={<Plus size={16} />}>
          Thêm thẻ mới
        </FcButton>
        {onOpenImportExcel && (
          <FcButton variant="success" onClick={onOpenImportExcel} icon={<FileSpreadsheet size={16} />}>
            Nhập từ Excel / CSV
          </FcButton>
        )}
      </FcEmpty>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-3">
      {/* Tìm kiếm và thống kê */}
      <FcCard padding="sm" className="flex flex-col items-center justify-between gap-3 !rounded-2xl sm:flex-row">
        <div className="relative w-full sm:w-80">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 dark:text-slate-400" aria-hidden="true" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Tìm kiếm từ vựng, nghĩa tiếng Việt..."
            aria-label="Tìm kiếm thẻ trong sổ"
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-10 pr-4 text-sm text-slate-800 transition-all focus:border-brand-500 focus:bg-white focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/40 dark:border-slate-600 dark:bg-slate-900/50 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-900"
          />
        </div>

        <span className="self-end text-xs font-medium text-slate-500 dark:text-slate-400 sm:self-center">
          Hiển thị <strong className="text-slate-700 dark:text-slate-200">{filteredCards.length}</strong> / {cards.length} thẻ từ vựng
        </span>
      </FcCard>

      {filteredCards.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center dark:border-slate-600 dark:bg-slate-800/60">
          <p className="text-sm text-slate-500 dark:text-slate-400">Không tìm thấy từ vựng nào khớp với từ khóa "{searchTerm}".</p>
        </div>
      ) : (
        <div className="h-[calc(100vh-340px)] [@supports(height:100dvh)]:h-[calc(100dvh-340px)] min-h-[320px] overflow-hidden rounded-2xl sm:min-h-[480px]">
          <Virtuoso
            style={{ height: "100%", width: "100%" }}
            totalCount={filteredCards.length}
            itemContent={(index) => {
              const card = filteredCards[index];
              const cardLang = card.lang_code || card.langCode || deckLang;

              return (
                <div className="pb-3 pr-1">
                  <FcCard padding="sm" className="!rounded-2xl hover:border-brand-200 hover:shadow-md dark:hover:border-slate-600">
                    <div className="mb-2 flex items-center justify-between">
                      <FcBadge tone="slate" className="uppercase tracking-wider">
                        {card.part_of_speech || card.partOfSpeech || "Từ vựng"}
                      </FcBadge>
                      <div className="flex items-center gap-0.5">
                        <button
                          type="button"
                          onClick={() => onPlayAudio(card.audio_url, card.term, cardLang, card.phonetic)}
                          className={`${ICON_BTN} text-brand-600 hover:bg-brand-50 dark:text-brand-300 dark:hover:bg-slate-700`}
                          title="Nghe phát âm"
                          aria-label={`Nghe phát âm ${card.term}`}
                        >
                          <Volume2 size={16} aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => onOpenEditCard(card)}
                          className={`${ICON_BTN} text-slate-500 hover:bg-brand-50 hover:text-brand-600 dark:hover:bg-slate-700 dark:hover:text-brand-300 dark:text-slate-400`}
                          title="Chỉnh sửa thẻ"
                          aria-label={`Chỉnh sửa thẻ ${card.term}`}
                        >
                          <Pencil size={16} aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => void onDeleteCard(card.id)}
                          className={`${ICON_BTN} text-slate-500 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400 dark:text-slate-400`}
                          title="Xóa thẻ"
                          aria-label={`Xóa thẻ ${card.term}`}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                        </button>
                      </div>
                    </div>

                    <h4 className="text-base font-bold text-slate-800 dark:text-slate-100" lang={cardLang}>{card.term}</h4>
                    {card.phonetic ? <p className="mb-1 font-mono text-xs text-brand-600 dark:text-brand-300">{card.phonetic}</p> : null}
                    <p className="mt-1 text-sm font-medium text-slate-600 dark:text-slate-300">{card.definition}</p>
                    {card.example_sentence || card.example ? (
                      <p className="mt-2 rounded-xl border border-slate-100 bg-slate-50 p-2.5 text-xs italic text-slate-500 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-400" lang={cardLang}>
                        "{card.example_sentence || card.example}"
                      </p>
                    ) : null}
                  </FcCard>
                </div>
              );
            }}
          />
        </div>
      )}
    </div>
  );
};
