import React, { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, Flame, Heart, Volume2, XCircle } from "lucide-react";
import {
  initSpeed, speedAnswer, speedMultiplier, speedNext, speedTimeUp, SPEED_CHALLENGE_LIVES, SPEED_CHALLENGE_SECONDS,
  type GameCard, type GameItemResult, type GameMode
} from "./gameLogic";
import { playSfx } from "./sfx";

interface SpeedRoundGameProps {
  cards: GameCard[];
  mode: GameMode;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onFinish: (items: GameItemResult[], durationMs: number) => void;
}

const AUTO_NEXT_CORRECT_MS = 600;
const AUTO_NEXT_WRONG_CHALLENGE_MS = 1000;

export const SpeedRoundGame: React.FC<SpeedRoundGameProps> = ({ cards, mode, onPlayAudio, onFinish }) => {
  const [state, setState] = useState(() => initSpeed(cards, mode));
  const [secondsLeft, setSecondsLeft] = useState(SPEED_CHALLENGE_SECONDS);
  const startedAt = useRef(Date.now());
  const finishedRef = useRef(false);

  const card = state.queue[state.index];

  // Đếm ngược 60 giây (Thử thách).
  useEffect(() => {
    if (mode !== "challenge" || state.finished) return;
    const t = window.setInterval(() => {
      const left = Math.max(0, SPEED_CHALLENGE_SECONDS - Math.floor((Date.now() - startedAt.current) / 1000));
      setSecondsLeft(left);
      if (left <= 0) setState((s) => speedTimeUp(s));
    }, 250);
    return () => window.clearInterval(t);
  }, [mode, state.finished]);

  useEffect(() => {
    if (state.finished && !finishedRef.current) {
      finishedRef.current = true;
      playSfx("win");
      onFinish(state.items, Date.now() - startedAt.current);
    }
  }, [state.finished, state.items, onFinish]);

  const next = useCallback(() => setState((s) => speedNext(s)), []);

  // Tự sang câu kế: đúng -> nhanh; Thử thách sai -> chờ ngắn; Thư giãn sai -> đợi người chơi bấm Tiếp tục.
  useEffect(() => {
    if (!state.answered) return;
    if (state.answered.correct) {
      const t = window.setTimeout(next, AUTO_NEXT_CORRECT_MS);
      return () => window.clearTimeout(t);
    }
    if (mode === "challenge") {
      const t = window.setTimeout(next, AUTO_NEXT_WRONG_CHALLENGE_MS);
      return () => window.clearTimeout(t);
    }
  }, [state.answered, mode, next]);

  const stateRef = useRef(state);
  stateRef.current = state;
  const choose = useCallback((choice: string) => {
    const current = stateRef.current;
    if (current.answered || current.finished) return;
    const after = speedAnswer(current, choice);
    playSfx(after.answered?.correct ? "correct" : "wrong");
    stateRef.current = after; // tránh hai lần bấm liên tiếp trước khi React kịp render
    setState(after);
  }, []);

  // Phím 1–4 chọn đáp án; Enter/Space sang câu kế (khi đang chờ ở chế độ Thư giãn).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (state.finished) return;
      if (!state.answered && /^[1-4]$/.test(e.key)) {
        const choice = state.choices[Number(e.key) - 1];
        if (choice) choose(choice);
      } else if (state.answered && !state.answered.correct && mode === "relax" && (e.key === "Enter" || e.key === " ")) {
        e.preventDefault();
        next();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state.finished, state.answered, state.choices, mode, choose, next]);

  if (!card) return null;
  const total = mode === "relax" ? state.queue.length : null;
  const pct = mode === "challenge" ? (secondsLeft / SPEED_CHALLENGE_SECONDS) * 100 : ((state.index + (state.answered ? 1 : 0)) / (total || 1)) * 100;

  return (
    <div className="w-full">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs font-bold">
        <span className="flex items-center gap-3 text-slate-600 dark:text-slate-300">
          <span data-testid="speed-score">Điểm: {state.score}</span>
          <span className={`flex items-center gap-1 ${state.combo >= 3 ? "text-orange-700 dark:text-orange-400" :"text-slate-500 dark:text-slate-400"}`} data-testid="speed-combo">
            <Flame size={14} /> Combo {state.combo}{state.combo >= 3 ? ` (×${speedMultiplier(state.combo)})` : ""}
          </span>
        </span>
        <span className="flex items-center gap-3 text-slate-600 dark:text-slate-300">
          {state.lives !== null && (
            <span className="flex items-center gap-0.5" aria-label={`Còn ${state.lives} mạng`} data-testid="speed-lives">
              {Array.from({ length: SPEED_CHALLENGE_LIVES }, (_, i) => (
                <Heart key={i} size={15} className={i < (state.lives ?? 0) ? "fill-rose-500 text-rose-500" : "text-slate-300 dark:text-slate-600"} />
              ))}
            </span>
          )}
          {mode === "challenge" ? <span data-testid="speed-timer">⏱ {secondsLeft}s</span> : <span>Câu {Math.min(state.index + 1, total!)}/{total}</span>}
        </span>
      </div>
      <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-brand-500 transition-all motion-reduce:transition-none" style={{ width: `${pct}%` }} />
      </div>

      <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-7 dark:border-slate-700 dark:bg-slate-800">
        <div className="mb-4 text-center">
          <h2 lang={card.lang_code} className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100" data-testid="speed-term">{card.term}</h2>
          {card.phonetic && <p className="mt-1 font-mono text-sm text-brand-600 dark:text-brand-400">{card.phonetic}</p>}
          <button
            type="button"
            onClick={() => onPlayAudio(card.audio_url ?? undefined, card.term, card.lang_code, card.phonetic ?? undefined)}
            className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 hover:bg-brand-100 dark:bg-brand-950/40 dark:text-brand-300 dark:hover:bg-brand-900/50"
          >
            <Volume2 size={14} /> Nghe
          </button>
        </div>

        <div className="grid gap-2.5" role="group" aria-label="Các đáp án">
          {state.choices.map((choice, index) => {
            const isAnswer = choice.trim().toLowerCase() === card.definition.trim().toLowerCase();
            const picked = state.answered?.choice === choice;
            let style = "border-slate-200 bg-white text-slate-700 hover:border-brand-300 hover:bg-brand-50/50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-brand-600 dark:hover:bg-slate-700";
            if (state.answered) {
              if (isAnswer) style = "border-emerald-400 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300";
              else if (picked) style = "border-rose-400 bg-rose-50 text-rose-800 motion-safe:animate-[shake_0.3s_ease-in-out] dark:bg-rose-950/40 dark:text-rose-300";
              else style = "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-600 dark:bg-slate-900/50 dark:text-slate-400";
            }
            return (
              <button
                key={`${state.index}-${index}`}
                type="button"
                disabled={!!state.answered}
                onClick={() => choose(choice)}
                className={`flex items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left text-sm font-semibold transition-all motion-reduce:transition-none ${style}`}
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-600 dark:bg-slate-700 dark:text-slate-300">{index + 1}</span>
                <span className="flex-1">{choice}</span>
                {state.answered && isAnswer && <CheckCircle2 size={18} className="text-emerald-600 dark:text-emerald-400" />}
                {state.answered && picked && !isAnswer && <XCircle size={18} className="text-rose-600 dark:text-rose-400" />}
              </button>
            );
          })}
        </div>

        {state.answered && !state.answered.correct && mode === "relax" && (
          <button type="button" autoFocus onClick={next} className="mt-4 w-full rounded-2xl bg-brand-600 py-3 text-sm font-bold text-white hover:bg-brand-700">
            Tiếp tục (Enter)
          </button>
        )}
      </div>
    </div>
  );
};
