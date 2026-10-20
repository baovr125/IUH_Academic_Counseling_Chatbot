import React, { useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, Volume2 } from "lucide-react";
import { initMatch, matchClearWrong, matchResults, matchSelect, type GameCard, type GameItemResult, type GameMode } from "./gameLogic";
import { playSfx } from "./sfx";

interface MatchPairsGameProps {
  cards: GameCard[];
  mode: GameMode;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onFinish: (items: GameItemResult[], durationMs: number) => void;
}

const WRONG_FLASH_MS = 650;

export const MatchPairsGame: React.FC<MatchPairsGameProps> = ({ cards, mode, onPlayAudio, onFinish }) => {
  const [state, setState] = useState(() => initMatch(cards));
  const startedAt = useRef(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const finishedRef = useRef(false);
  const byId = useMemo(() => new Map(cards.map((c) => [c.id, c])), [cards]);

  // Đồng hồ (chỉ hiển thị ở chế độ Thử thách; Thư giãn không bấm giờ).
  useEffect(() => {
    if (mode !== "challenge" || state.done) return;
    const t = window.setInterval(() => setElapsed(Math.floor((Date.now() - startedAt.current) / 1000)), 500);
    return () => window.clearInterval(t);
  }, [mode, state.done]);

  useEffect(() => {
    if (!state.lastWrong) return;
    const t = window.setTimeout(() => setState((s) => matchClearWrong(s)), WRONG_FLASH_MS);
    return () => window.clearTimeout(t);
  }, [state.lastWrong]);

  const onFinishRef = useRef(onFinish);
  onFinishRef.current = onFinish;
  const resultsRef = useRef(state);
  resultsRef.current = state;
  useEffect(() => {
    if (state.done && !finishedRef.current) {
      finishedRef.current = true;
      playSfx("win");
      // Dừng một nhịp để người chơi kịp thấy cặp cuối biến mất. Không hủy timer khi render lại.
      window.setTimeout(() => onFinishRef.current(matchResults(resultsRef.current), Date.now() - startedAt.current), 700);
    }
  }, [state.done]);

  const pick = (side: "term" | "def", id: string) => {
    const before = state;
    const after = matchSelect(state, side, id);
    if (after === before) return;
    if (side === "term") {
      const card = byId.get(id);
      if (card && after.selectedTerm === id) onPlayAudio(card.audio_url ?? undefined, card.term, card.lang_code, card.phonetic ?? undefined);
    }
    if (after.matched.length > before.matched.length) playSfx("correct");
    else if (after.lastWrong && !before.lastWrong) playSfx("wrong");
    setState(after);
  };

  const cell = (side: "term" | "def", id: string, label: string) => {
    const matched = state.matched.includes(id);
    const selected = side === "term" ? state.selectedTerm === id : state.selectedDef === id;
    const wrong = !!state.lastWrong && (side === "term" ? state.lastWrong.term === id : state.lastWrong.def === id);
    let style = "border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:bg-blue-50/60 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-blue-600 dark:hover:bg-slate-700";
    if (matched) style = "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300";
    else if (wrong) style = "border-rose-400 bg-rose-50 text-rose-800 motion-safe:animate-[shake_0.3s_ease-in-out] dark:bg-rose-950/40 dark:text-rose-300";
    else if (selected) style = "border-blue-500 bg-blue-50 text-blue-800 ring-2 ring-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:ring-blue-800";
    return (
      <button
        key={`${side}-${id}`}
        type="button"
        data-testid={`match-${side}-${id}`}
        disabled={matched}
        aria-pressed={selected}
        onClick={() => pick(side, id)}
        className={`flex min-h-[3.25rem] w-full items-center justify-between gap-2 rounded-2xl border-2 px-3 py-2.5 text-left text-sm font-semibold transition-all motion-reduce:transition-none ${style}`}
      >
        <span lang={side === "term" ? byId.get(id)?.lang_code : undefined} className="break-words">{label}</span>
        {matched ? <CheckCircle2 size={16} className="shrink-0" /> : side === "term" ? <Volume2 size={14} className="shrink-0 text-slate-300 dark:text-slate-600" /> : null}
      </button>
    );
  };

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
        <span data-testid="match-progress">Đã ghép {state.matched.length}/{state.cards.length}</span>
        <span className="flex items-center gap-3">
          <span>Lỗi: {state.mistakes}</span>
          {mode === "challenge" && <span aria-label="Thời gian">⏱ {elapsed}s</span>}
        </span>
      </div>
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">Chạm một từ rồi chạm nghĩa tương ứng (hoặc ngược lại).</p>
      <div className="grid grid-cols-2 gap-3 sm:gap-5">
        <div className="flex flex-col gap-2.5" aria-label="Từ">{state.cards.map((c) => cell("term", c.id, c.term))}</div>
        <div className="flex flex-col gap-2.5" aria-label="Nghĩa">
          {state.defOrder.map((id) => cell("def", id, byId.get(id)?.definition ?? ""))}
        </div>
      </div>
    </div>
  );
};
