import React, { useState, useMemo } from "react";
import { Virtuoso } from "react-virtuoso";
import { Volume2, Pencil, Trash2, Search, RefreshCw, Plus, FileSpreadsheet } from "lucide-react";
import type { BackendCardItem, BackendDeck } from "../../services/flashcardService";

interface CardListViewProps {
  deck: BackendDeck;
  cards: BackendCardItem[];
  isLoading: boolean;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onOpenEditCard: (card: BackendCardItem) => void;
  onDeleteCard: (cardId: string) => Promise<void>;
  onOpenAddCard: () => void;
  onOpenImportExcel?: () => void;
}

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
      <div className="flex flex-1 items-center justify-center p-12 min-h-[350px]">
        <RefreshCw size={32} className="animate-spin text-blue-600" />
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-200 p-12 text-center bg-white min-h-[300px] flex flex-col items-center justify-center">
        <p className="text-sm font-semibold text-slate-700">Chưa có thẻ từ vựng nào trong danh sách</p>
        <p className="text-xs text-slate-400 mt-1">Bấm nút "Thêm từ" hoặc "Nhập Excel" để tạo danh sách từ vựng cho sổ này.</p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={onOpenAddCard}
            className="flex items-center gap-2 rounded-2xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition-colors"
          >
            <Plus size={15} />
            <span>Thêm thẻ mới</span>
          </button>
          {onOpenImportExcel && (
            <button
              type="button"
              onClick={onOpenImportExcel}
              className="flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs font-bold text-emerald-700 shadow-sm hover:bg-emerald-100 transition-colors"
            >
              <FileSpreadsheet size={15} />
              <span>Nhập từ Excel / CSV</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-3">
      {/* Search and Stats Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Tìm kiếm từ vựng, nghĩa tiếng Việt..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-2 text-xs focus:border-blue-500 focus:bg-white focus:outline-none transition-all"
          />
        </div>

        <span className="text-xs font-medium text-slate-500 self-end sm:self-center">
          Hiển thị <strong>{filteredCards.length}</strong> / {cards.length} thẻ từ vựng
        </span>
      </div>

      {/* Virtualized Cards List */}
      {filteredCards.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center bg-white">
          <p className="text-xs text-slate-500">Không tìm thấy từ vựng nào khớp với từ khóa "{searchTerm}".</p>
        </div>
      ) : (
        <div className="rounded-2xl overflow-hidden" style={{ height: "calc(100vh - 280px)", minHeight: "480px" }}>
          <Virtuoso
            style={{ height: "100%", width: "100%" }}
            totalCount={filteredCards.length}
            itemContent={(index) => {
              const card = filteredCards[index];
              const cardLang = card.lang_code || card.langCode || deckLang;

              return (
                <div className="pb-3 pr-1">
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm hover:shadow-md hover:border-blue-200 transition-all flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                          {card.part_of_speech || card.partOfSpeech || "Từ vựng"}
                        </span>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => onPlayAudio(card.audio_url, card.term, cardLang, card.phonetic)}
                            className="rounded-full p-1.5 text-blue-600 hover:bg-blue-50 transition-colors"
                            title="Nghe phát âm"
                          >
                            <Volume2 size={15} />
                          </button>
                          <button
                            type="button"
                            onClick={() => onOpenEditCard(card)}
                            className="rounded-full p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                            title="Chỉnh sửa thẻ"
                          >
                            <Pencil size={15} />
                          </button>
                          <button
                            type="button"
                            onClick={() => onDeleteCard(card.id)}
                            className="rounded-full p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            title="Xóa thẻ"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </div>

                      <h4 className="text-base font-bold text-slate-800">{card.term}</h4>
                      {card.phonetic ? (
                        <p className="text-xs font-mono text-blue-600 mb-1">{card.phonetic}</p>
                      ) : null}
                      <p className="text-xs text-slate-600 mt-1 font-medium">{card.definition}</p>
                      {card.example_sentence || card.example ? (
                        <p className="text-[11px] italic text-slate-500 mt-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                          "{card.example_sentence || card.example}"
                        </p>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            }}
          />
        </div>
      )}
    </div>
  );
};
