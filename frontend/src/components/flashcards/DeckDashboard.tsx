import React from "react";
import { ArrowRight, BookOpen, FileSpreadsheet, Library, Pencil, Plus, Trash2, Zap } from "lucide-react";
import { LANG_CONFIG, isLearnableLang, normalizeLangCode } from "../../services/deckStorage";
import type { BackendDeck } from "../../services/flashcardService";
import { FcBadge, FcButton, FcCard, FcEmpty, FcLoading, FcMenu, FcSkeleton, LangFlag } from "./ui";

interface DeckDashboardProps {
  decks: BackendDeck[];
  isLoading: boolean;
  onSelectDeck: (deck: BackendDeck) => void;
  onOpenCreateDeck: () => void;
  onOpenGenerate: (deck?: BackendDeck) => void;
  onOpenCatalog: () => void;
  onOpenEditDeck: (deck: BackendDeck) => void;
  onOpenDeleteDeck: (deck: BackendDeck) => void;
  onOpenImportExcel: (deck: BackendDeck) => void;
  /** Có giá trị = đang xem bộ sưu tập của một ngôn ngữ: bỏ tiêu đề lớn, tạo sổ theo ngôn ngữ đó. */
  lang?: string;
}

export const DeckDashboard: React.FC<DeckDashboardProps> = ({
  decks,
  isLoading,
  onSelectDeck,
  onOpenCreateDeck,
  onOpenGenerate,
  onOpenCatalog,
  onOpenEditDeck,
  onOpenDeleteDeck,
  onOpenImportExcel,
  lang
}) => {
  const embedded = !!lang;
  // Thư viện bộ từ (catalog) hiện chỉ có nội dung tiếng Anh; trình sinh từ bằng AI dùng được cho cả 9 ngôn ngữ học (không gồm tiếng Việt).
  const showEnglishTools = !lang || lang === "en";
  const showAiTool = !lang || isLearnableLang(lang);
  const viName = lang ? LANG_CONFIG[lang]?.viName : undefined;

  return (
    <div className={embedded ? "flex w-full flex-col" : "mx-auto flex w-full max-w-5xl flex-col p-8"}>
      {/* Thanh công cụ */}
      <div className={`${embedded ? "mb-5 sm:justify-end" : "mb-8 sm:justify-between"} flex flex-col gap-4 sm:flex-row sm:items-center`}>
        {!embedded && (
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
              <span>Sổ Thẻ Từ Vựng & Lặp Ngắt Quãng (FSRS)</span>
              <FcBadge tone="blue">Spaced Repetition</FcBadge>
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Học từ vựng thông minh qua phát âm chuẩn bản xứ, câu ngữ cảnh và thử thách gõ chính tả ngẫu nhiên.
            </p>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2">
          {showEnglishTools && (
            <FcButton variant="secondary" onClick={onOpenCatalog} icon={<Library size={16} />}>
              Thư viện bộ từ
            </FcButton>
          )}
          {showAiTool && (
            <FcButton variant="soft" onClick={() => onOpenGenerate()} icon={<Zap size={16} />}>
              Tạo từ vựng với AI
            </FcButton>
          )}
          <FcButton variant="primary" onClick={onOpenCreateDeck} icon={<Plus size={16} />}>
            {viName ? `Tạo sổ ${viName} mới` : "Tạo Sổ Thẻ Mới"}
          </FcButton>
        </div>
      </div>

      {isLoading ? (
        <FcLoading label="Đang tải sổ thẻ" className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((n) => (
            <FcCard key={n} padding="md" className="space-y-4">
              <FcSkeleton className="h-9 w-12" />
              <FcSkeleton className="h-5 w-3/4" />
              <FcSkeleton className="h-4 w-full" />
              <FcSkeleton className="h-4 w-1/2" />
            </FcCard>
          ))}
        </FcLoading>
      ) : decks.length === 0 ? (
        <FcEmpty
          icon={<BookOpen size={30} />}
          title={viName ? `Chưa có sổ ${viName} nào` : "Chưa có sổ từ vựng nào"}
          description={
            viName
              ? `Tạo một sổ mới, hoặc dịch một từ ${viName} ở Dịch thuật rồi bấm “Lưu Flashcard” — sổ mặc định sẽ được tạo tự động.`
              : "Hãy tạo một sổ từ vựng mới hoặc vào tính năng Dịch tài liệu để hệ thống tự động bóc tách từ vựng chuyên ngành vào sổ thẻ của bạn."
          }
        >
          {showAiTool && (
            <FcButton variant="primary" onClick={() => onOpenGenerate()} icon={<Zap size={16} />}>
              Nhờ AI tạo bộ từ vựng đầu tiên
            </FcButton>
          )}
          {showEnglishTools && (
            <FcButton variant="soft" onClick={onOpenCatalog} icon={<Library size={16} />}>
              Khám phá thư viện bộ từ
            </FcButton>
          )}
          <FcButton variant="secondary" onClick={onOpenCreateDeck} icon={<Plus size={16} />}>
            Tạo sổ thẻ trống
          </FcButton>
        </FcEmpty>
      ) : (
        <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {decks.map((deck) => {
            const code = normalizeLangCode(deck.lang_code || deck.langCode) ?? lang ?? null;
            const count = deck.cards_count ?? 0;
            return (
              <FcCard
                key={deck.id}
                as="li"
                padding="none"
                interactive
                // Chuột: bấm bất kỳ đâu trên thẻ để mở sổ. Bàn phím: dùng nút "Mở sổ" bên dưới (Enter/Space nổi bọt lên thẻ).
                onClick={() => onSelectDeck(deck)}
                className="group relative flex cursor-pointer flex-col focus-within:z-20 hover:z-10"
              >
                <div className="flex items-start justify-between gap-3 p-5 pb-0">
                  <LangFlag lang={code} size="lg" />
                  <FcMenu
                    label={`Tùy chọn sổ ${deck.title}`}
                    items={[
                      { key: "ai", label: "Thêm từ vựng bằng AI", icon: <Zap size={16} />, onClick: () => onOpenGenerate(deck), hidden: !(showAiTool && isLearnableLang(code)) },
                      { key: "import", label: "Nhập từ Excel / CSV", icon: <FileSpreadsheet size={16} />, onClick: () => onOpenImportExcel(deck) },
                      { key: "edit", label: "Chỉnh sửa sổ thẻ", icon: <Pencil size={16} />, onClick: () => onOpenEditDeck(deck) },
                      { key: "delete", label: "Xóa sổ thẻ", icon: <Trash2 size={16} />, onClick: () => onOpenDeleteDeck(deck), tone: "danger" }
                    ]}
                  />
                </div>

                <div className="flex-1 px-5 pt-4">
                  <h3 className="line-clamp-1 text-base font-bold text-slate-800 transition-colors group-hover:text-brand-600 dark:text-slate-100 dark:group-hover:text-brand-300">
                    {deck.title}
                  </h3>
                  <p className="mt-1.5 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">
                    {deck.description || `Sổ từ vựng ${(code && LANG_CONFIG[code]?.label) || "Ngoại ngữ"}`}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <FcBadge tone="blue">{count} thẻ</FcBadge>
                    {count === 0 && <FcBadge tone="amber">Trống</FcBadge>}
                    {deck.is_default && <FcBadge tone="slate">Mặc định</FcBadge>}
                  </div>
                </div>

                <div className="mt-5 border-t border-slate-100 px-5 py-4 dark:border-slate-700">
                  <button
                    type="button"
                    aria-label={`Mở sổ ${deck.title}`}
                    className="flex items-center gap-1.5 rounded-lg text-sm font-semibold text-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-brand-300"
                  >
                    {count === 0 ? "Mở sổ để thêm từ" : "Bắt đầu học FSRS"}
                    <ArrowRight size={15} className="transition-transform group-hover:translate-x-1" aria-hidden="true" />
                  </button>
                </div>
              </FcCard>
            );
          })}
        </ul>
      )}
    </div>
  );
};
