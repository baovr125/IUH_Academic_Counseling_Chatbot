import React, { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Crosshair, Gamepad2, Loader2, Puzzle, Star, Timer, Type, Volume2, VolumeX } from "lucide-react";
import { useAuth } from "../../../hooks/useAuth";
import {
  fetchGameCards, fetchGameStats, submitGameSession, type BackendDeck, type GameSessionResponse, type GameStats
} from "../../../services/flashcardService";
import { newRequestId } from "../../../services/flashcardSave";
import { normalizeLangCode } from "../../../services/deckStorage";
import { MatchPairsGame } from "./MatchPairsGame";
import { SpeedRoundGame } from "./SpeedRoundGame";
import { WordBuilderGame } from "./WordBuilderGame";
import { ShooterGame } from "./ShooterGame";
import { GAME_TITLES, GameResult } from "./GameResult";
import { isMuted, setMuted } from "./sfx";
import type { GameCard, GameItemResult, GameKind, GameMode } from "./gameLogic";

interface GamesHubProps {
  deck: BackendDeck;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
}

export const GAME_STATS_KEY = "flashcard_game_stats";
const PREF_KEY = "iuh_flashcard_game_prefs";
const BUILDER_LANGS = ["en", "de", "fr", "es", "ru"];

interface Prefs {
  mode: GameMode;
  applyReview: boolean;
}

function loadPrefs(): Prefs {
  try {
    const raw = JSON.parse(localStorage.getItem(PREF_KEY) || "{}");
    return { mode: raw.mode === "challenge" ? "challenge" : "relax", applyReview: raw.applyReview !== false };
  } catch {
    return { mode: "relax", applyReview: true };
  }
}

const GAME_INFO: Record<GameKind, { icon: React.ReactNode; blurb: string; hint: string }> = {
  match: { icon: <Puzzle size={26} />, blurb: "Nối từ với nghĩa. Khởi động nhẹ nhàng, hợp mọi ngôn ngữ.", hint: "6 cặp" },
  speed: { icon: <Timer size={26} />, blurb: "Trả lời trắc nghiệm liên tiếp để lên combo và nhân điểm.", hint: "Thư giãn: 10 câu · Thử thách: 60 giây, 3 mạng" },
  builder: { icon: <Type size={26} />, blurb: "Xếp các chữ cái bị xáo trộn thành từ đúng. Chỉ cho ngôn ngữ chữ cái.", hint: "10 từ" },
  shooter: { icon: <Crosshair size={26} />, blurb: "Súng nạp một từ: bắn trúng bóng chứa nghĩa đúng trước khi chúng rơi xuống.", hint: "Cần ≥5 thẻ · Thư giãn: bóng rơi chậm · Thử thách: 3 mạng" }
};

type View = "menu" | "loading" | "playing" | "result";

export const GamesHub: React.FC<GamesHubProps> = ({ deck, onPlayAudio }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const lang = normalizeLangCode(deck.lang_code || deck.langCode) ?? undefined;

  const [prefs, setPrefsState] = useState<Prefs>(loadPrefs);
  const [muted, setMutedState] = useState(isMuted());
  const [view, setView] = useState<View>("menu");
  const [game, setGame] = useState<GameKind>("match");
  const [cards, setCards] = useState<GameCard[]>([]);
  const [runId, setRunId] = useState(0);
  const [menuError, setMenuError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [response, setResponse] = useState<GameSessionResponse | null>(null);
  const pending = useRef<{ items: GameItemResult[]; durationMs: number; requestId: string } | null>(null);
  const levelBefore = useRef<number | undefined>(undefined);

  const statsQuery = useQuery({
    queryKey: [GAME_STATS_KEY, user?.id || "guest", lang],
    staleTime: 0,
    queryFn: async (): Promise<GameStats> => {
      const res = await fetchGameStats(lang);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });
  const stats = statsQuery.data;

  const setPrefs = (next: Prefs) => {
    setPrefsState(next);
    try {
      localStorage.setItem(PREF_KEY, JSON.stringify(next));
    } catch {
      /* bỏ qua */
    }
  };

  const start = useCallback(async (kind: GameKind) => {
    setGame(kind);
    setMenuError(null);
    setView("loading");
    const res = await fetchGameCards(kind, deck.id);
    if (!res.ok) {
      setMenuError(res.error.code === "MIGRATION_REQUIRED" ? res.error.message : res.error.message || "Không tải được bộ thẻ cho trò chơi.");
      setView("menu");
      return;
    }
    if (!res.data.playable) {
      setMenuError(res.data.reason || "Sổ này chưa đủ thẻ để chơi trò này.");
      setView("menu");
      return;
    }
    levelBefore.current = stats?.level.level;
    setCards(res.data.cards.map((c) => ({ ...c })));
    setRunId((n) => n + 1);
    setResponse(null);
    setSubmitError(null);
    setView("playing");
  }, [deck.id, stats?.level.level]);

  const submit = useCallback(async (payload: { items: GameItemResult[]; durationMs: number; requestId: string }) => {
    pending.current = payload;
    setView("result");
    setSubmitting(true);
    setSubmitError(null);
    const res = await submitGameSession({
      clientRequestId: payload.requestId,
      game,
      mode: prefs.mode,
      deckId: deck.id,
      durationMs: payload.durationMs,
      items: payload.items,
      applyReview: prefs.applyReview
    });
    setSubmitting(false);
    if (!res.ok) {
      setSubmitError(res.error.message);
      return;
    }
    setResponse(res.data);
    void queryClient.invalidateQueries({ queryKey: [GAME_STATS_KEY] });
    // Lịch ôn có thể đã đổi: làm mới hàng đợi/thống kê học của sổ.
    void queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
    void queryClient.invalidateQueries({ queryKey: ["flashcard_language_summary"] });
  }, [game, prefs.mode, prefs.applyReview, deck.id, queryClient]);

  const handleFinish = useCallback((items: GameItemResult[], durationMs: number) => {
    void submit({ items, durationMs, requestId: newRequestId() });
  }, [submit]);

  const builderBlocked = !!lang && !BUILDER_LANGS.includes(lang);

  // ---------------------------------------------------------------- đang chơi / kết quả
  if (view === "playing" || view === "result") {
    return (
      <div className={`mx-auto w-full ${game === "shooter" ? "max-w-3xl" : "max-w-2xl"}`} data-testid="game-stage">
        <div className="mb-4 flex items-center justify-between">
          <button type="button" onClick={() => setView("menu")} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700">
            <ArrowLeft size={14} /> {view === "playing" ? "Thoát ván" : "Danh sách trò chơi"}
          </button>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-500 dark:text-slate-400">
            <span>{GAME_TITLES[game]} · {prefs.mode === "challenge" ? "Thử thách" : "Thư giãn"}</span>
            <button
              type="button"
              aria-label={muted ? "Bật âm thanh hiệu ứng" : "Tắt âm thanh hiệu ứng"}
              onClick={() => { setMuted(!muted); setMutedState(!muted); }}
              className="rounded-full p-1.5 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
            >
              {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
          </div>
        </div>

        {view === "playing" ? (
          game === "match" ? (
            <MatchPairsGame key={runId} cards={cards} mode={prefs.mode} onPlayAudio={onPlayAudio} onFinish={handleFinish} />
          ) : game === "speed" ? (
            <SpeedRoundGame key={runId} cards={cards} mode={prefs.mode} onPlayAudio={onPlayAudio} onFinish={handleFinish} />
          ) : game === "shooter" ? (
            <ShooterGame key={runId} cards={cards} mode={prefs.mode} onPlayAudio={onPlayAudio} onFinish={handleFinish} />
          ) : (
            <WordBuilderGame key={runId} cards={cards} onPlayAudio={onPlayAudio} onFinish={handleFinish} />
          )
        ) : (
          <GameResult
            game={game}
            submitting={submitting}
            error={submitError}
            response={response}
            levelBefore={levelBefore.current}
            onRetrySubmit={() => pending.current && void submit(pending.current)}
            onPlayAgain={() => void start(game)}
            onBack={() => setView("menu")}
          />
        )}
      </div>
    );
  }

  // ---------------------------------------------------------------- menu
  const level = stats?.level;
  const levelPct = level ? Math.min(100, ((level.xp - level.level_floor_xp) / Math.max(1, level.next_level_xp - level.level_floor_xp)) * 100) : 0;

  return (
    <div className="mx-auto w-full max-w-5xl">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-violet-100 bg-gradient-to-r from-violet-50 to-blue-50 p-4 dark:border-violet-900/50 dark:from-violet-950/40 dark:to-blue-950/40">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-600 text-white"><Gamepad2 size={22} /></div>
          <div>
            <p className="text-sm font-extrabold text-slate-800 dark:text-slate-100" data-testid="game-level">
              {level ? `Cấp ${level.level}` : statsQuery.isLoading ? "Đang tải…" : "Trò chơi ôn từ"}
            </p>
            {level && (
              <div className="mt-1 flex items-center gap-2">
                <div className="h-1.5 w-32 overflow-hidden rounded-full bg-white dark:bg-slate-800" role="progressbar" aria-valuenow={Math.round(levelPct)} aria-valuemin={0} aria-valuemax={100}>
                  <div className="h-full rounded-full bg-violet-500" style={{ width: `${levelPct}%` }} />
                </div>
                <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">{level.xp}/{level.next_level_xp} XP</span>
              </div>
            )}
          </div>
        </div>
        <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">{stats ? `Hôm nay: ${stats.plays_today} ván` : ""}</p>
      </div>

      {statsQuery.isError && (
        <p role="alert" className="mb-3 rounded-xl border border-amber-200 bg-amber-50 p-2.5 text-xs font-semibold text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          {(statsQuery.error as Error).message} (Vẫn chơi được, nhưng chưa hiển thị kỷ lục.)
        </p>
      )}

      <div className="mb-5 flex flex-wrap items-center gap-x-6 gap-y-3 rounded-2xl border border-slate-200 bg-white p-3.5 dark:border-slate-600 dark:bg-slate-800">
        <div className="flex items-center gap-2" role="radiogroup" aria-label="Chế độ chơi">
          {([["relax", "Thư giãn", "Không bấm giờ"], ["challenge", "Thử thách", "Có giờ, combo, mạng"]] as const).map(([value, label, sub]) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={prefs.mode === value}
              onClick={() => setPrefs({ ...prefs, mode: value })}
              className={`rounded-xl border px-3 py-1.5 text-left text-xs font-bold transition-colors ${prefs.mode === value ? "border-violet-500 bg-violet-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"}`}
            >
              {label}
              <span className={`block text-[10px] font-medium ${prefs.mode === value ? "text-violet-100" : "text-slate-500 dark:text-slate-400"}`}>{sub}</span>
            </button>
          ))}
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
          <input
            type="checkbox"
            checked={prefs.applyReview}
            onChange={(e) => setPrefs({ ...prefs, applyReview: e.target.checked })}
            className="h-4 w-4 rounded border-slate-300 text-violet-600 dark:border-slate-600 dark:text-violet-400"
          />
          Tính vào lịch ôn
          <span className="text-[10px] font-normal text-slate-500 dark:text-slate-400">(chỉ thẻ đã đến hạn)</span>
        </label>
        <button
          type="button"
          aria-label={muted ? "Bật âm thanh hiệu ứng" : "Tắt âm thanh hiệu ứng"}
          onClick={() => { setMuted(!muted); setMutedState(!muted); }}
          className="ml-auto rounded-full p-1.5 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>
      </div>

      {menuError && (
        <div role="alert" className="mb-4 flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs font-semibold text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200" data-testid="games-menu-error">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" /> {menuError}
        </div>
      )}

      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {(["match", "speed", "builder", "shooter"] as const).map((kind) => {
          const blocked = kind === "builder" && builderBlocked;
          // Dùng ?. vì máy chủ cũ (chưa có trò mới) có thể chưa trả số liệu của trò đó.
          const best = stats?.games?.[kind]?.best?.[prefs.mode];
          return (
            <li key={kind} className="flex">
              <button
                type="button"
                data-testid={`game-card-${kind}`}
                disabled={blocked || view === "loading"}
                onClick={() => void start(kind)}
                className="group flex w-full flex-col rounded-3xl border border-slate-200/80 bg-white p-5 text-left shadow-sm transition-all hover:-translate-y-1 hover:border-violet-300 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-violet-600"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-600 group-hover:bg-violet-100 dark:bg-violet-950/40 dark:text-violet-400">{GAME_INFO[kind].icon}</span>
                <span className="mt-3 text-base font-extrabold text-slate-800 dark:text-slate-100">{GAME_TITLES[kind]}</span>
                <span className="mt-1 text-xs text-slate-500 dark:text-slate-400">{GAME_INFO[kind].blurb}</span>
                <span className="mt-2 text-[11px] font-medium text-slate-500 dark:text-slate-400">{GAME_INFO[kind].hint}</span>
                <span className="mt-auto pt-3 text-xs font-bold text-slate-600 dark:text-slate-300">
                  {blocked ? (
                    <span className="text-amber-700 dark:text-amber-300">Không hỗ trợ ngôn ngữ này</span>
                  ) : best ? (
                    <span className="flex items-center gap-1" data-testid={`game-best-${kind}`}>
                      <Star size={13} className="fill-amber-400 text-amber-400" /> Kỷ lục {best.score}
                    </span>
                  ) : (
                    <span className="text-slate-500 dark:text-slate-400">Chưa có kỷ lục</span>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {view === "loading" && (
        <p className="mt-4 flex items-center justify-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400" role="status">
          <Loader2 size={14} className="animate-spin" /> Đang chuẩn bị ván chơi…
        </p>
      )}
    </div>
  );
};
