import React, { useCallback, useEffect, useRef, useState } from "react";
import { Crosshair, Heart, Pause, Play, Volume2 } from "lucide-react";
import type { GameCard, GameItemResult, GameMode } from "./gameLogic";
import {
  ARENA, CANNON, bubblePos, currentWord, fireAt, fireAtBubble, initShooter, liveBubbles, stepShooter, CHALLENGE_LIVES,
  type ShooterEvent, type ShooterState
} from "./shooterLogic";
import { speedMultiplier } from "./gameLogic";
import { playSfx } from "./sfx";

interface ShooterGameProps {
  cards: GameCard[];
  mode: GameMode;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onFinish: (items: GameItemResult[], durationMs: number) => void;
}

const prefersReducedMotion = () =>
  typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const isTouchDevice = () =>
  typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(pointer: coarse)").matches;

const raf = (cb: (ts: number) => void): number =>
  typeof window.requestAnimationFrame === "function" ? window.requestAnimationFrame(cb) : (setTimeout(() => cb(performance.now()), 16) as unknown as number);
const caf = (id: number) => (typeof window.cancelAnimationFrame === "function" ? window.cancelAnimationFrame(id) : clearTimeout(id));

export const ShooterGame: React.FC<ShooterGameProps> = ({ cards, mode, onPlayAudio, onFinish }) => {
  const reduced = useRef(prefersReducedMotion()).current;
  const stateRef = useRef<ShooterState>(initShooter(cards, mode, { reducedMotion: reduced }));
  const [view, setView] = useState<ShooterState>(stateRef.current);
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const [assist, setAssist] = useState(isTouchDevice);
  const [aim, setAim] = useState({ x: CANNON.x, y: 10 });
  const [selected, setSelected] = useState<string | null>(null);
  const arenaRef = useRef<HTMLDivElement | null>(null);
  const finishedRef = useRef(false);
  const onFinishRef = useRef(onFinish);
  onFinishRef.current = onFinish;
  const audioRef = useRef(onPlayAudio);
  audioRef.current = onPlayAudio;

  const commit = useCallback((next: ShooterState) => {
    stateRef.current = next;
    setView(next);
  }, []);

  const handleEvents = useCallback((events: ShooterEvent[], s: ShooterState) => {
    for (const e of events) {
      if (e.type === "pop") {
        playSfx("correct");
        // Từ vừa bắn trúng (súng đã nạp từ kế tiếp nên không dùng wordIndex hiện tại).
        const w = s.words.find((x) => x.id === e.bubbleId);
        if (w) audioRef.current(w.audio_url ?? undefined, w.term, w.lang_code, w.phonetic ?? undefined);
      } else if (e.type === "wrong" || e.type === "miss") playSfx("wrong");
      else if (e.type === "fire") playSfx("tick");
      else if (e.type === "end") playSfx("win");
    }
  }, []);

  // Vòng lặp: tính chuyển động theo thời gian thật; dừng khi tạm dừng hoặc tab bị ẩn.
  useEffect(() => {
    let id = 0;
    let last = 0;
    const frame = (ts: number) => {
      id = raf(frame);
      if (!last) last = ts;
      let remaining = Math.min((ts - last) / 1000, 0.25);
      last = ts;
      if (pausedRef.current || stateRef.current.phase === "finished") return;
      let s = stateRef.current;
      const collected: ShooterEvent[] = [];
      while (remaining > 1e-6) {
        const dt = Math.min(remaining, 0.05);
        remaining -= dt;
        s = stepShooter(s, dt);
        collected.push(...s.events);
      }
      if (s !== stateRef.current) {
        handleEvents(collected, s);
        commit({ ...s, events: collected });
      }
    };
    id = raf(frame);
    return () => caf(id);
  }, [commit, handleEvents]);

  useEffect(() => {
    if (view.phase === "finished" && !finishedRef.current) {
      finishedRef.current = true;
      onFinishRef.current(view.items, Math.round(view.t * 1000));
    }
  }, [view.phase, view.items, view.t]);

  const setPause = useCallback((value: boolean) => {
    pausedRef.current = value;
    setPaused(value);
  }, []);

  useEffect(() => {
    const onHide = () => {
      if (document.hidden) setPause(true);
    };
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, [setPause]);

  const shoot = useCallback((x: number, y: number) => {
    if (pausedRef.current) return;
    const before = stateRef.current;
    const after = fireAt(before, x, y);
    if (after !== before) {
      handleEvents(after.events, after);
      commit(after);
    }
  }, [commit, handleEvents]);

  // Ngắm hỗ trợ / bàn phím: đạn nhắm đúng bóng được chọn và bay xuyên các bóng khác.
  const shootBubble = useCallback((bubbleId: string) => {
    if (pausedRef.current) return;
    const before = stateRef.current;
    const after = fireAtBubble(before, bubbleId);
    if (after !== before) {
      handleEvents(after.events, after);
      commit(after);
    }
  }, [commit, handleEvents]);

  const toArena = (e: { clientX: number; clientY: number }) => {
    const rect = arenaRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0 || rect.height === 0) return null;
    return { x: ((e.clientX - rect.left) / rect.width) * ARENA, y: ((e.clientY - rect.top) / rect.height) * ARENA };
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const p = toArena(e);
    if (p) setAim(p);
  };

  const onArenaClick = (e: React.MouseEvent) => {
    const bubbleEl = (e.target as HTMLElement).closest("[data-bubble-id]") as HTMLElement | null;
    if (assist && bubbleEl) {
      shootBubble(bubbleEl.dataset.bubbleId!);
      return;
    }
    const p = toArena(e);
    if (p) {
      setAim(p);
      shoot(p.x, p.y);
    } else if (bubbleEl) {
      shootBubble(bubbleEl.dataset.bubbleId!); // không đo được kích thước sân: dùng ngắm hỗ trợ
    }
  };

  // Bàn phím: ←/→ chọn bóng, Enter/Space bắn bóng đang chọn, 1–5 bắn nhanh bóng thứ n (trái -> phải), P/Esc tạm dừng.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const s = stateRef.current;
      if (s.phase === "finished" || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === "p" || e.key === "P" || e.key === "Escape") {
        e.preventDefault();
        setPause(!pausedRef.current);
        return;
      }
      if (pausedRef.current) return;
      const live = liveBubbles(s);
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault();
        if (live.length === 0) return;
        const index = live.findIndex((b) => b.id === selected);
        const nextIndex = index < 0 ? (e.key === "ArrowRight" ? 0 : live.length - 1) : (index + (e.key === "ArrowRight" ? 1 : -1) + live.length) % live.length;
        setSelected(live[nextIndex].id);
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const target = live.find((b) => b.id === selected) ?? live[0];
        if (target) shootBubble(target.id);
      } else if (/^[1-5]$/.test(e.key)) {
        const target = live[Number(e.key) - 1];
        if (target) {
          setSelected(target.id);
          shootBubble(target.id);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, setPause, shootBubble]);

  const word = currentWord(view);
  if (!word) return null;
  const angle = Math.atan2(aim.y - CANNON.y, aim.x - CANNON.x) * (180 / Math.PI) + 90;
  const clamped = Math.max(-80, Math.min(80, angle));

  return (
    <div className="w-full select-none">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs font-bold text-slate-600 dark:text-slate-300">
        <span className="flex items-center gap-3">
          <span data-testid="shooter-score">Điểm: {view.score}</span>
          <span className={view.combo >= 3 ? "text-orange-700 dark:text-orange-400" :"text-slate-500 dark:text-slate-400"} data-testid="shooter-combo">
            Combo {view.combo}{view.combo >= 3 ? ` (×${speedMultiplier(view.combo)})` : ""}
          </span>
        </span>
        <span className="flex items-center gap-3">
          {view.lives !== null && (
            <span className="flex items-center gap-0.5" aria-label={`Còn ${view.lives} mạng`} data-testid="shooter-lives">
              {Array.from({ length: CHALLENGE_LIVES }, (_, i) => (
                <Heart key={i} size={15} className={i < (view.lives ?? 0) ? "fill-rose-500 text-rose-500" : "text-slate-300 dark:text-slate-600"} />
              ))}
            </span>
          )}
          <span data-testid="shooter-progress">Từ {Math.min(view.wordIndex + 1, view.words.length)}/{view.words.length}</span>
          <button
            type="button"
            aria-pressed={assist}
            onClick={() => setAssist((v) => !v)}
            title="Ngắm hỗ trợ: chạm vào bóng nào thì bắn thẳng vào bóng đó"
            className={`flex items-center gap-1 rounded-full border px-2.5 py-1 ${assist ? "border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-700 dark:bg-brand-950/40 dark:text-brand-300" : "border-slate-200 bg-white text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400"}`}
          >
            <Crosshair size={12} /> Ngắm hỗ trợ
          </button>
          <button type="button" onClick={() => setPause(!paused)} aria-label={paused ? "Tiếp tục" : "Tạm dừng"} className="rounded-full border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
            {paused ? <Play size={13} /> : <Pause size={13} />}
          </button>
        </span>
      </div>

      <div
        ref={arenaRef}
        data-testid="shooter-arena"
        data-theme-lock="dark"
        onPointerMove={onPointerMove}
        onClick={onArenaClick}
        className="relative aspect-[5/4] w-full cursor-crosshair touch-none overflow-hidden rounded-3xl border border-brand-900/40 bg-gradient-to-b from-brand-950 via-slate-900 to-slate-950 shadow-inner"
        style={{ containerType: "inline-size" }}
      >
        {/* vạch báo nguy hiểm */}
        <div className="pointer-events-none absolute left-0 right-0 border-t border-dashed border-rose-400/40" style={{ top: "84%" }} aria-hidden />

        {view.bubbles.map((b) => {
          const p = bubblePos(b, view.t, view.reducedMotion);
          const shaking = b.shakeUntil > view.t;
          const isSelected = selected === b.id;
          const size = b.radius * 2;
          let tone = "from-sky-600 to-brand-700 text-white";
          if (b.popped) tone = "from-emerald-300 to-emerald-500 text-white scale-150 opacity-0";
          else if (b.revealed) tone = "from-emerald-600 to-emerald-800 text-white ring-4 ring-emerald-200";
          else if (shaking) tone = "from-rose-600 to-rose-700 text-white";
          return (
            <button
              key={b.id}
              type="button"
              tabIndex={-1}
              data-bubble-id={b.id}
              data-testid={`shooter-bubble-${b.id}`}
              aria-label={b.text}
              title={b.text}
              disabled={b.popped}
              className={`absolute flex items-center justify-center overflow-hidden rounded-full bg-gradient-to-br p-0.5 text-center font-semibold leading-[1.1] shadow-lg transition-[transform,opacity] duration-300 motion-reduce:transition-none ${tone} ${
                isSelected ? "outline outline-4 outline-offset-2 outline-amber-300" : ""
              } ${shaking ? "motion-safe:animate-[shake_0.3s_ease-in-out]" : ""}`}
              style={{ left: `${p.x}%`, top: `${p.y}%`, width: `${size}%`, aspectRatio: "1 / 1", fontSize: "clamp(8px, 1.45cqw, 12px)", transform: `translate(-50%, -50%)${b.popped ? " scale(1.5)" : ""}` }}
            >
              <span className="line-clamp-3 break-words">{b.text}</span>
            </button>
          );
        })}

        {view.bullet && (
          <span
            data-testid="shooter-bullet"
            className="pointer-events-none absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-300 shadow-[0_0_10px_3px_rgba(252,211,77,0.8)]"
            style={{ left: `${view.bullet.x}%`, top: `${view.bullet.y}%` }}
          />
        )}

        {/* khẩu súng và từ đang nạp */}
        <div className="pointer-events-none absolute" style={{ left: `${CANNON.x}%`, top: `${CANNON.y}%`, transform: "translate(-50%, -50%)" }}>
          <div className="absolute bottom-1/2 left-1/2 h-12 w-3 origin-bottom -translate-x-1/2 rounded-t-full bg-gradient-to-t from-slate-500 to-slate-300" style={{ transform: `translateX(-50%) rotate(${clamped}deg)` }} aria-hidden />
          <div className="relative flex h-10 w-10 items-center justify-center rounded-full border-4 border-slate-500 bg-slate-700" aria-hidden />
        </div>
        {/* Tấm từ đang nạp luôn trắng trên đấu trường tối ở cả hai chế độ nên KHÔNG được có biến thể dark:
            (data-theme-lock được tests/themeLock.test.tsx kiểm tra; công cụ sửa hàng loạt cũng phải bỏ qua khối này). */}
        <div data-theme-lock="light" className="absolute bottom-1 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-2xl bg-white/95 px-3 py-1.5 shadow-lg">
          <span lang={word.lang_code} className="text-base font-extrabold text-slate-800 sm:text-lg" data-testid="shooter-word">{word.term}</span>
          {word.phonetic && <span className="hidden font-mono text-xs text-brand-600 sm:inline">{word.phonetic}</span>}
          <button
            type="button"
            aria-label="Nghe phát âm"
            onClick={(e) => { e.stopPropagation(); onPlayAudio(word.audio_url ?? undefined, word.term, word.lang_code, word.phonetic ?? undefined); }}
            className="pointer-events-auto rounded-full bg-brand-50 p-1 text-brand-700 hover:bg-brand-100"
          >
            <Volume2 size={14} />
          </button>
        </div>

        {paused && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setPause(false); }}
            className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-950/75 text-white"
            data-testid="shooter-paused"
          >
            <Play size={40} />
            <span className="text-sm font-bold">Tạm dừng — bấm để tiếp tục</span>
          </button>
        )}
      </div>

      <p className="mt-2 text-center text-xs sm:text-[11px] text-slate-500 dark:text-slate-400">
        {reduced ? "Chế độ giảm chuyển động: bóng đứng yên. " : ""}
        Bắn vào bóng có <strong>nghĩa đúng</strong> của từ trên súng; mỗi lần bắn đúng sẽ thêm một bóng mới. Bắn sai chỉ mất combo. Phím: ←/→ chọn · Enter/Space bắn · 1–5 bắn nhanh · P tạm dừng
      </p>
    </div>
  );
};
