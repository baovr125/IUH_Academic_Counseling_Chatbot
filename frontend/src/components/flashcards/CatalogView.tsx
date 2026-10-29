import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, ArrowLeft, BookMarked, CheckCircle2, Eye, Library, Plus, Search } from "lucide-react";
import {
  cloneCatalogDeck,
  fetchCatalogDecks,
  fetchCatalogPreview,
  type BackendDeck,
  type CatalogDeck
} from "../../services/flashcardService";
import { FcBadge, FcButton, FcCard, FcEmpty, FcLoading, FcModal, FcPage, FcSkeleton } from "./ui";

interface CatalogViewProps {
  onBack: () => void;
  /** Mở sổ thẻ (đã có hoặc vừa được thêm) để học. */
  onOpenDeck: (deck: BackendDeck) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  communication: "Giao tiếp cơ bản",
  food: "Ăn uống",
  going_out: "Đi chơi & du lịch",
  home_health: "Nhà cửa & sức khỏe"
};

export const categoryLabel = (code?: string | null): string => (code ? CATEGORY_LABELS[code] || code : "Khác");

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

const FIELD =
  "rounded-xl border border-slate-200 bg-white text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/40 " +
  "dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500";

const ERROR_BOX =
  "flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300";

export const CatalogView: React.FC<CatalogViewProps> = ({ onBack, onOpenDeck }) => {
  const queryClient = useQueryClient();
  const [category, setCategory] = useState<string>("");
  const [level, setLevel] = useState<string>("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 400);
    return () => window.clearTimeout(timer);
  }, [search]);

  const catalogQuery = useQuery({
    queryKey: ["flashcard_catalog", category, level, debouncedSearch],
    queryFn: async (): Promise<CatalogDeck[]> => {
      const res = await fetchCatalogDecks({
        category: category || undefined,
        level: level || undefined,
        q: debouncedSearch || undefined
      });
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });

  // Danh sách nhóm lấy từ toàn bộ thư viện (không lọc) để chip không biến mất khi đang lọc.
  const allQuery = useQuery({
    queryKey: ["flashcard_catalog", "", "", ""],
    queryFn: async (): Promise<CatalogDeck[]> => {
      const res = await fetchCatalogDecks();
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });
  const categories = Array.from(new Set((allQuery.data || []).map((d) => d.category).filter(Boolean))) as string[];

  const cloneMutation = useMutation({
    mutationFn: async (deck: CatalogDeck) => {
      const res = await cloneCatalogDeck(deck.id);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["flashcard_decks"] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_catalog"] });
      onOpenDeck(result.deck);
    },
    onError: (error: Error) => setActionError(error.message),
    onSettled: () => setAddingId(null)
  });

  const handleAdd = (deck: CatalogDeck) => {
    setActionError(null);
    if (deck.added_deck_id) {
      onOpenDeck({ id: deck.added_deck_id, title: deck.title, description: deck.description, lang_code: deck.lang_code, cards_count: deck.cards_count });
      return;
    }
    setAddingId(deck.id);
    cloneMutation.mutate(deck);
  };

  const decks = catalogQuery.data || [];

  return (
    <FcPage width="lg">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-lg shadow-brand-600/30" aria-hidden="true">
            <Library size={22} />
          </span>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Thư viện bộ từ</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Các bộ từ vựng theo chủ đề đời sống hằng ngày. Thêm vào sổ của bạn để học theo lịch FSRS riêng.
            </p>
          </div>
        </div>
        <FcButton variant="secondary" onClick={onBack} icon={<ArrowLeft size={16} />}>
          Quay lại Sổ thẻ
        </FcButton>
      </div>

      {/* Bộ lọc */}
      <div className="mb-5 flex flex-col gap-3">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Lọc theo nhóm chủ đề">
          {[""].concat(categories).map((c) => (
            <button
              key={c || "all"}
              type="button"
              aria-pressed={category === c}
              onClick={() => setCategory(c)}
              className={`rounded-full px-4 py-1.5 [@media(pointer:coarse)]:min-h-[44px] text-xs font-bold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                category === c
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
              }`}
            >
              {c ? categoryLabel(c) : "Tất cả"}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="relative min-w-[200px] flex-1">
            <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 dark:text-slate-400" aria-hidden="true" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm bộ từ..."
              aria-label="Tìm bộ từ"
              className={`${FIELD} w-full py-2.5 pl-10 pr-3`}
            />
          </label>
          <select value={level} onChange={(e) => setLevel(e.target.value)} aria-label="Lọc theo trình độ" className={`${FIELD} px-3.5 py-2.5 font-semibold`}>
            <option value="">Mọi trình độ</option>
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>
      </div>

      {actionError && (
        <div role="alert" className={`mb-4 ${ERROR_BOX} text-xs`}>
          <AlertCircle size={16} className="mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span>{actionError}</span>
        </div>
      )}

      {catalogQuery.isLoading ? (
        <FcLoading label="Đang tải thư viện bộ từ" className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((n) => (
            <FcCard key={n} className="space-y-4">
              <FcSkeleton className="h-5 w-1/2" />
              <FcSkeleton className="h-5 w-3/4" />
              <FcSkeleton className="h-12 w-full" />
              <FcSkeleton className="h-9 w-full" />
            </FcCard>
          ))}
        </FcLoading>
      ) : catalogQuery.isError ? (
        <div role="alert" className={ERROR_BOX}>
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span>{(catalogQuery.error as Error).message}</span>
        </div>
      ) : decks.length === 0 ? (
        <FcEmpty
          icon={<BookMarked size={30} />}
          title="Chưa có bộ từ phù hợp"
          description="Thử bỏ bớt bộ lọc, hoặc quay lại sau khi thư viện được bổ sung."
        />
      ) : (
        <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {decks.map((deck) => {
            const added = !!deck.added_deck_id;
            const adding = addingId === deck.id;
            return (
              <FcCard key={deck.id} as="li" interactive className="flex flex-col justify-between">
                <div>
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <FcBadge tone="blue">{categoryLabel(deck.category)}</FcBadge>
                    {deck.level && <FcBadge tone="amber">{deck.level}</FcBadge>}
                    <FcBadge tone="slate">{deck.cards_count} từ</FcBadge>
                  </div>
                  <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">{deck.title}</h3>
                  <p className="mt-1.5 line-clamp-3 text-sm text-slate-500 dark:text-slate-400">{deck.description}</p>
                </div>
                <div className="mt-5 flex items-center gap-2">
                  <FcButton
                    variant="secondary"
                    size="sm"
                    onClick={() => setPreviewId(deck.id)}
                    aria-label={`Xem trước ${deck.title}`}
                    title="Xem trước"
                    className="shrink-0"
                  >
                    <Eye size={16} aria-hidden="true" />
                  </FcButton>
                  <FcButton
                    variant={added ? "success" : "primary"}
                    size="sm"
                    loading={adding}
                    onClick={() => handleAdd(deck)}
                    icon={added ? <CheckCircle2 size={14} /> : <Plus size={14} />}
                    className="flex-1 whitespace-nowrap"
                  >
                    {adding ? "Đang thêm..." : added ? "Đã thêm - Mở sổ" : "Thêm vào sổ của tôi"}
                  </FcButton>
                </div>
              </FcCard>
            );
          })}
        </ul>
      )}

      {previewId && <PreviewDialog deckId={previewId} onClose={() => setPreviewId(null)} />}
    </FcPage>
  );
};

const PreviewDialog: React.FC<{ deckId: string; onClose: () => void }> = ({ deckId, onClose }) => {
  const previewQuery = useQuery({
    queryKey: ["flashcard_catalog_preview", deckId],
    queryFn: async () => {
      const res = await fetchCatalogPreview(deckId, 12);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });
  const data = previewQuery.data;

  return (
    <FcModal
      title="Xem trước bộ từ"
      size="lg"
      onClose={onClose}
      description={data ? `${data.deck.title} · ${data.cards.length}/${data.deck.cards_count} từ đầu tiên` : undefined}
    >
      {previewQuery.isLoading ? (
        <FcLoading label="Đang tải bản xem trước" className="flex flex-col gap-3">
          <FcSkeleton className="h-16 w-full" />
          <FcSkeleton className="h-16 w-full" />
          <FcSkeleton className="h-16 w-full" />
        </FcLoading>
      ) : previewQuery.isError ? (
        <p role="alert" className="text-sm text-rose-600 dark:text-rose-400">
          {(previewQuery.error as Error).message}
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {data?.cards.map((c) => (
            <li key={c.term} className="rounded-2xl border border-slate-100 bg-slate-50/60 p-3 dark:border-slate-700 dark:bg-slate-900/40">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">{c.term}</span>
                {c.phonetic && <span className="font-mono text-xs text-brand-600 dark:text-brand-300">{c.phonetic}</span>}
                {c.part_of_speech && <span className="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">{c.part_of_speech}</span>}
              </div>
              <p className="text-sm text-slate-700 dark:text-slate-300">{c.definition}</p>
              {c.example && (
                <p className="mt-1 text-xs italic text-slate-500 dark:text-slate-400">
                  "{c.example}"{c.example_translation && <span className="block not-italic text-slate-500 dark:text-slate-400">{c.example_translation}</span>}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </FcModal>
  );
};
