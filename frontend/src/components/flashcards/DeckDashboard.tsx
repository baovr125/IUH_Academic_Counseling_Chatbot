import React from "react";
import { Plus, BookOpen, Pencil, Trash2, RefreshCw, FileSpreadsheet } from "lucide-react";
import { LANG_CONFIG } from "../../services/deckStorage";
import type { BackendDeck } from "../../services/flashcardService";

interface DeckDashboardProps {
  decks: BackendDeck[];
  isLoading: boolean;
  onSelectDeck: (deck: BackendDeck) => void;
  onOpenCreateDeck: () => void;
  onOpenEditDeck: (deck: BackendDeck) => void;
  onOpenDeleteDeck: (deck: BackendDeck) => void;
  onOpenImportExcel: (deck: BackendDeck) => void;
}

export const DeckDashboard: React.FC<DeckDashboardProps> = ({
  decks,
  isLoading,
  onSelectDeck,
  onOpenCreateDeck,
  onOpenEditDeck,
  onOpenDeleteDeck,
  onOpenImportExcel
}) => {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col p-8">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Sổ Thẻ Từ Vựng & Lặp Ngắt Quãng (FSRS)</span>
            <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-bold text-blue-600 border border-blue-200">
              Spaced Repetition
            </span>
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Học từ vựng thông minh qua phát âm chuẩn bản xứ, câu ngữ cảnh và thử thách gõ chính tả ngẫu nhiên.
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenCreateDeck}
          className="flex items-center gap-2 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-sm hover:bg-blue-700 transition-all hover:scale-105"
        >
          <Plus size={18} />
          <span>Tạo Sổ Thẻ Mới</span>
        </button>
      </div>

      {/* Decks Grid */}
      {isLoading ? (
        <div className="flex flex-1 items-center justify-center min-h-[300px]">
          <RefreshCw size={36} className="animate-spin text-blue-600" />
        </div>
      ) : decks.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center min-h-[300px]">
          <BookOpen size={56} className="mb-4 text-slate-300" />
          <h3 className="text-lg font-bold text-slate-800">Chưa có sổ từ vựng nào</h3>
          <p className="mt-1 max-w-md text-xs text-slate-500">
            Hãy tạo một sổ từ vựng mới hoặc vào tính năng Dịch tài liệu để hệ thống tự động bóc tách từ vựng chuyên ngành vào sổ thẻ của bạn.
          </p>
          <button
            type="button"
            onClick={onOpenCreateDeck}
            className="mt-6 flex items-center gap-2 rounded-2xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-blue-700"
          >
            <Plus size={16} />
            <span>Tạo sổ thẻ đầu tiên</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {decks.map((deck) => {
            const langMeta = LANG_CONFIG[deck.lang_code || deck.langCode || "en"] || { flag: "🌐", label: "Ngoại ngữ" };
            return (
              <div
                key={deck.id}
                onClick={() => onSelectDeck(deck)}
                className="group relative flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-blue-300 hover:shadow-md cursor-pointer"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-3xl">{deck.icon_flag || langMeta.flag}</span>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                        {deck.cards_count !== undefined ? deck.cards_count : 0} thẻ
                      </span>
                      {/* Import Excel, Edit & Delete Action Buttons */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenImportExcel(deck);
                        }}
                        className="rounded-full p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                        title="Nhập từ vựng từ Excel / CSV"
                      >
                        <FileSpreadsheet size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenEditDeck(deck);
                        }}
                        className="rounded-full p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        title="Chỉnh sửa sổ thẻ"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenDeleteDeck(deck);
                        }}
                        className="rounded-full p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Xóa sổ thẻ"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-slate-800 group-hover:text-blue-600 transition-colors line-clamp-1">
                    {deck.title}
                  </h3>
                  <p className="mt-1.5 text-xs text-slate-500 line-clamp-2">
                    {deck.description || `Sổ từ vựng ${langMeta.label}`}
                  </p>
                </div>

                <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-100">
                  <span className="text-xs font-semibold text-blue-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    Bắt đầu học FSRS &rarr;
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
