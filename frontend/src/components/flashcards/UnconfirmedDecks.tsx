import React, { useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { LANG_CONFIG, LEARNABLE_LANGS } from "../../services/deckStorage";
import { setDeckLanguage, type UnconfirmedDeck } from "../../services/flashcardService";
import { invalidateFlashcardQueries } from "../../services/flashcardSave";

interface UnconfirmedDecksProps {
  decks: UnconfirmedDeck[];
  onOpenDeck: (deck: UnconfirmedDeck) => void;
}

/**
 * Sổ thẻ cũ chưa rõ ngôn ngữ. Hệ thống KHÔNG tự đoán: người dùng xác nhận ngôn ngữ thì sổ (và mọi thẻ trong đó)
 * mới được đưa vào bộ sưu tập tương ứng.
 */
export const UnconfirmedDecks: React.FC<UnconfirmedDecksProps> = ({ decks, onOpenDeck }) => {
  const [choice, setChoice] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (decks.length === 0) return null;

  const confirm = async (deck: UnconfirmedDeck) => {
    const lang = choice[deck.id];
    if (!lang) return;
    setBusy(deck.id);
    setError(null);
    const res = await setDeckLanguage(deck.id, lang);
    setBusy(null);
    if (!res.ok) {
      setError(res.error.message);
      return;
    }
    invalidateFlashcardQueries(deck.id);
  };

  return (
    <section aria-labelledby="unconfirmed-heading" className="mt-8 rounded-3xl border border-amber-200 bg-amber-50/60 p-5 dark:border-amber-900/60 dark:bg-amber-950/20">
      <h3 id="unconfirmed-heading" className="flex items-center gap-2 text-sm font-bold text-amber-900 dark:text-amber-200">
        <AlertTriangle size={16} /> Cần xác nhận ngôn ngữ ({decks.length} sổ)
      </h3>
      <p className="mt-1 text-xs text-amber-800 dark:text-amber-300/90">
        Các sổ này được tạo trước khi có bộ sưu tập theo ngôn ngữ nên chưa rõ ngôn ngữ. Hãy chọn đúng ngôn ngữ để đưa chúng vào bộ sưu tập.
      </p>
      {error && <p role="alert" className="mt-2 text-xs font-semibold text-red-600 dark:text-red-400">{error}</p>}

      <ul className="mt-3 flex flex-col gap-2">
        {decks.map((deck) => (
          <li key={deck.id} className="flex flex-wrap items-center gap-3 rounded-2xl border border-amber-200 bg-white p-3 dark:border-amber-900/60 dark:bg-slate-800">
            <button type="button" onClick={() => onOpenDeck(deck)} className="min-w-0 flex-1 text-left">
              <span className="block truncate text-sm font-bold text-slate-800 hover:text-blue-600 dark:text-slate-100 dark:hover:text-blue-300">{deck.title}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">{deck.cards_count} thẻ</span>
            </button>
            <label className="sr-only" htmlFor={`unconfirmed-${deck.id}`}>Ngôn ngữ của sổ {deck.title}</label>
            <select
              id={`unconfirmed-${deck.id}`}
              value={choice[deck.id] ?? ""}
              onChange={(e) => setChoice((c) => ({ ...c, [deck.id]: e.target.value }))}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            >
              <option value="">Chọn ngôn ngữ…</option>
              {LEARNABLE_LANGS.map((code) => (
                <option key={code} value={code}>
                  {LANG_CONFIG[code].viName}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void confirm(deck)}
              disabled={!choice[deck.id] || busy === deck.id}
              className="flex items-center gap-1.5 rounded-xl bg-amber-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-amber-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 disabled:opacity-50 dark:focus-visible:ring-offset-slate-900"
            >
              {busy === deck.id && <Loader2 size={13} className="animate-spin" />}
              Xác nhận
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
};
