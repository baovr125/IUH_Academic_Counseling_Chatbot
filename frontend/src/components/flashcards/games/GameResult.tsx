import React from "react";
import { AlertTriangle, Loader2, RotateCcw, Sparkles, Star, Trophy } from "lucide-react";
import type { GameSessionResponse } from "../../../services/flashcardService";
import type { GameKind } from "./gameLogic";

export const GAME_TITLES: Record<GameKind, string> = {
  match: "Ghép cặp",
  speed: "Đua 60 giây",
  builder: "Xếp chữ",
  shooter: "Bắn bóng nghĩa"
};

interface GameResultProps {
  game: GameKind;
  /** Đang gửi kết quả lên máy chủ. */
  submitting: boolean;
  error: string | null;
  response: GameSessionResponse | null;
  levelBefore?: number;
  onRetrySubmit: () => void;
  onPlayAgain: () => void;
  onBack: () => void;
}

export const GameResult: React.FC<GameResultProps> = ({ game, submitting, error, response, levelBefore, onRetrySubmit, onPlayAgain, onBack }) => {
  if (submitting) {
    return (
      <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 text-sm font-semibold text-slate-500 dark:text-slate-400" role="status">
        <Loader2 className="animate-spin text-brand-600 dark:text-brand-400" size={30} />
        Đang chấm điểm…
      </div>
    );
  }

  if (error || !response) {
    return (
      <div className="mx-auto max-w-md rounded-3xl border border-amber-200 bg-amber-50 p-6 text-center dark:border-amber-800 dark:bg-amber-950/40" role="alert">
        <AlertTriangle className="mx-auto mb-2 text-amber-500" size={32} />
        <h3 className="text-base font-bold text-amber-900 dark:text-amber-200">Chưa lưu được kết quả</h3>
        <p className="mt-1 text-xs text-amber-800 dark:text-amber-300">{error || "Không có phản hồi từ máy chủ."} Điểm và lịch ôn chưa được cập nhật.</p>
        <div className="mt-4 flex justify-center gap-2">
          <button type="button" onClick={onRetrySubmit} className="rounded-xl bg-amber-700 px-4 py-2 [@media(pointer:coarse)]:min-h-[44px] text-xs font-bold text-white hover:bg-amber-800">Thử gửi lại</button>
          <button type="button" onClick={onBack} className="rounded-xl border border-amber-300 bg-white px-4 py-2 [@media(pointer:coarse)]:min-h-[44px] text-xs font-bold text-amber-800 hover:bg-amber-100 dark:border-amber-700 dark:bg-slate-800 dark:text-amber-300 dark:hover:bg-amber-900/50">Bỏ qua</button>
        </div>
      </div>
    );
  }

  const s = response.session;
  const leveledUp = !!response.level && levelBefore !== undefined && response.level.level > levelBefore;
  return (
    <div className="mx-auto max-w-md rounded-3xl border border-slate-200/80 bg-white p-6 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800" data-testid="game-result">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{GAME_TITLES[game]} · {s.mode === "challenge" ? "Thử thách" : "Thư giãn"}</p>
      <div className="my-3 flex justify-center gap-1.5" aria-label={`${s.stars} trên 3 sao`} data-testid="game-stars">
        {[1, 2, 3].map((n) => (
          <Star key={n} size={38} className={n <= s.stars ? "fill-amber-400 text-amber-400" : "text-slate-200 dark:text-slate-600"} />
        ))}
      </div>
      <p className="text-4xl font-extrabold text-slate-800 dark:text-slate-100" data-testid="game-score">{s.score}</p>
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">điểm</p>

      {response.is_record && (
        <p className="mx-auto mt-3 flex w-fit items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800 dark:bg-amber-900/40 dark:text-amber-300" data-testid="game-record">
          <Trophy size={14} /> Kỷ lục mới!{response.previous_best ? ` (trước đó ${response.previous_best})` : ""}
        </p>
      )}
      {leveledUp && (
        <p className="mx-auto mt-2 flex w-fit items-center gap-1.5 rounded-full bg-brand-100 px-3 py-1 text-xs font-bold text-brand-800 dark:bg-brand-900/40 dark:text-brand-300" data-testid="game-levelup">
          <Sparkles size={14} /> Lên cấp {response.level!.level}!
        </p>
      )}

      <dl className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <div className="rounded-2xl bg-slate-50 p-2.5 dark:bg-slate-900/50"><dt className="text-slate-500 dark:text-slate-400">Đúng</dt><dd className="text-base font-bold text-slate-800 dark:text-slate-100">{s.correct}/{s.total}</dd></div>
        <div className="rounded-2xl bg-slate-50 p-2.5 dark:bg-slate-900/50"><dt className="text-slate-500 dark:text-slate-400">Lỗi</dt><dd className="text-base font-bold text-slate-800 dark:text-slate-100">{s.mistakes}</dd></div>
        <div className="rounded-2xl bg-slate-50 p-2.5 dark:bg-slate-900/50"><dt className="text-slate-500 dark:text-slate-400">XP</dt><dd className="text-base font-bold text-brand-700 dark:text-brand-300">+{s.xp}</dd></div>
      </dl>
      {(game === "speed" || game === "shooter") && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Combo cao nhất: {s.best_combo}</p>}
      {game === "builder" && s.hints > 0 && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Gợi ý đã dùng: {s.hints}</p>}

      <p className="mt-3 text-xs sm:text-[11px] text-slate-500 dark:text-slate-400" data-testid="game-review-note">
        {s.applied_review
          ? s.reviewed_count > 0
            ? `Đã cập nhật lịch ôn cho ${s.reviewed_count} thẻ đến hạn.`
            : "Không có thẻ nào đến hạn trong ván này nên lịch ôn không đổi."
          : "Ván này không tính vào lịch ôn."}
      </p>

      <div className="mt-5 flex justify-center gap-2">
        <button type="button" onClick={onPlayAgain} className="flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-brand-700">
          <RotateCcw size={14} /> Chơi lại
        </button>
        <button type="button" onClick={onBack} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
          Chọn trò khác
        </button>
      </div>
    </div>
  );
};
