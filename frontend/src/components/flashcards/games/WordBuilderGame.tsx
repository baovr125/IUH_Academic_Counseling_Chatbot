import React, { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, Delete, Lightbulb, SkipForward, Volume2 } from "lucide-react";
import {
  BUILDER_MAX_HINTS_PER_WORD, builderClearWrong, builderHint, builderNext, builderPlace, builderSkip, builderUndo, builderWord,
  initBuilder, type GameCard, type GameItemResult
} from "./gameLogic";
import { playSfx } from "./sfx";

interface WordBuilderGameProps {
  cards: GameCard[];
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onFinish: (items: GameItemResult[], durationMs: number) => void;
}

const WRONG_FLASH_MS = 700;

export const WordBuilderGame: React.FC<WordBuilderGameProps> = ({ cards, onPlayAudio, onFinish }) => {
  const [state, setState] = useState(() => initBuilder(cards));
  const stateRef = useRef(state);
  stateRef.current = state;
  const startedAt = useRef(Date.now());
  const finishedRef = useRef(false);

  const card = state.words[state.index];
  const word = builderWord(state);

  const update = useCallback((fn: (s: typeof state) => typeof state) => {
    const before = stateRef.current;
    const after = fn(before);
    if (after === before) return;
    if (after.solved && !before.solved) {
      playSfx("correct");
      const c = after.words[after.index];
      onPlayAudio(c.audio_url ?? undefined, c.term, c.lang_code, c.phonetic ?? undefined);
    } else if (after.wrong && !before.wrong) playSfx("wrong");
    else if (after.placed.length > before.placed.length) playSfx("tick");
    stateRef.current = after;
    setState(after);
  }, [onPlayAudio]);

  useEffect(() => {
    if (!state.wrong) return;
    const t = window.setTimeout(() => update(builderClearWrong), WRONG_FLASH_MS);
    return () => window.clearTimeout(t);
  }, [state.wrong, update]);

  useEffect(() => {
    if (state.finished && !finishedRef.current) {
      finishedRef.current = true;
      playSfx("win");
      onFinish(state.items, Date.now() - startedAt.current);
    }
  }, [state.finished, state.items, onFinish]);

  // Bàn phím: gõ chữ để đặt ô tương ứng; Backspace hoàn tác; Enter sang từ kế khi đã đúng.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const s = stateRef.current;
      if (s.finished || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === "Backspace") {
        e.preventDefault();
        update(builderUndo);
      } else if (e.key === "Enter" && s.solved) {
        e.preventDefault();
        update((x) => builderNext(x));
      } else if (Array.from(e.key).length === 1 && !s.solved) {
        const tile = s.tiles.find((t) => !s.placed.includes(t.id) && t.ch.toLowerCase() === e.key.toLowerCase());
        if (tile) update((x) => builderPlace(x, tile.id));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [update]);

  if (!card) return null;
  const slots = Array.from(word);
  const letterAt = (i: number) => {
    const id = state.placed[i];
    return id === undefined ? "" : state.tiles.find((t) => t.id === id)?.ch ?? "";
  };
  const hintsLeft = BUILDER_MAX_HINTS_PER_WORD - state.hints;

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
        <span data-testid="builder-progress">Từ {state.index + 1}/{state.words.length}</span>
        <span>Gợi ý đã dùng: {state.hints}</span>
      </div>
      <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700" role="progressbar" aria-valuenow={Math.round((state.index / state.words.length) * 100)} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-blue-500 transition-all motion-reduce:transition-none" style={{ width: `${(state.index / state.words.length) * 100}%` }} />
      </div>

      <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-7 dark:border-slate-700 dark:bg-slate-800">
        <div className="mb-5 text-center">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Xếp chữ cái thành từ có nghĩa</p>
          <h2 className="mt-1 text-2xl font-extrabold text-slate-800 dark:text-slate-100" data-testid="builder-meaning">{card.definition}</h2>
          {card.part_of_speech && <span className="mt-1 inline-block rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-bold uppercase text-slate-600 dark:bg-slate-700 dark:text-slate-300">{card.part_of_speech}</span>}
          <div>
            <button
              type="button"
              onClick={() => onPlayAudio(card.audio_url ?? undefined, card.term, card.lang_code, card.phonetic ?? undefined)}
              className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50"
            >
              <Volume2 size={14} /> Nghe từ
            </button>
          </div>
        </div>

        <div
          className={`mb-5 flex flex-wrap justify-center gap-2 ${state.wrong ? "motion-safe:animate-[shake_0.3s_ease-in-out]" : ""}`}
          aria-label="Từ đang xếp"
          data-testid="builder-slots"
        >
          {slots.map((_, i) => {
            const ch = letterAt(i);
            const style = state.solved
              ? "border-emerald-400 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
              : state.wrong
              ? "border-rose-400 bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300"
              : ch
              ? "border-blue-400 bg-blue-50 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
              : "border-dashed border-slate-300 bg-slate-50 text-transparent dark:border-slate-600 dark:bg-slate-900/50";
            return (
              <span key={i} lang={card.lang_code} className={`flex h-12 w-10 items-center justify-center rounded-xl border-2 text-xl font-extrabold sm:h-14 sm:w-12 ${style}`}>
                {ch || "·"}
              </span>
            );
          })}
        </div>

        {state.solved ? (
          <div className="flex flex-col items-center gap-3">
            <p className="flex items-center gap-1.5 text-sm font-bold text-emerald-700 dark:text-emerald-300" role="status"><CheckCircle2 size={18} /> Chính xác!</p>
            <button type="button" autoFocus onClick={() => update((s) => builderNext(s))} className="w-full rounded-2xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700">
              {state.index + 1 >= state.words.length ? "Xem kết quả (Enter)" : "Từ kế tiếp (Enter)"}
            </button>
          </div>
        ) : (
          <>
            <div className="mb-4 flex flex-wrap justify-center gap-2" role="group" aria-label="Các chữ cái">
              {state.tiles.map((t) => {
                const used = state.placed.includes(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    disabled={used || state.wrong}
                    onClick={() => update((s) => builderPlace(s, t.id))}
                    lang={card.lang_code}
                    className={`flex h-12 w-10 items-center justify-center rounded-xl border-2 text-xl font-extrabold shadow-sm transition-all motion-reduce:transition-none sm:h-14 sm:w-12 ${
                      used ? "border-slate-100 bg-slate-50 text-slate-200 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-600" : "border-slate-300 bg-white text-slate-800 hover:-translate-y-0.5 hover:border-blue-400 hover:shadow dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                    }`}
                  >
                    {t.ch}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button type="button" onClick={() => update(builderUndo)} disabled={state.placed.length === 0 || state.wrong} className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
                <Delete size={14} /> Xóa chữ cuối
              </button>
              <button type="button" onClick={() => update(builderHint)} disabled={hintsLeft <= 0 || state.wrong} className="flex items-center gap-1.5 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-bold text-amber-700 hover:bg-amber-100 disabled:opacity-40 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300 dark:hover:bg-amber-900/50">
                <Lightbulb size={14} /> Gợi ý ({hintsLeft})
              </button>
              <button type="button" onClick={() => update((s) => builderSkip(s))} className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-500 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700">
                <SkipForward size={14} /> Bỏ qua
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
