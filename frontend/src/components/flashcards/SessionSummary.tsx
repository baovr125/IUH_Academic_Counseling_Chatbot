import React from "react";
import { ArrowLeft, Clock, PartyPopper, RotateCcw, Sparkles, Target, Trophy, Volume2 } from "lucide-react";
import type { StudyStats } from "../../services/flashcardService";
import { FcButton, FcCard, FcStat } from "./ui";

export interface SessionResult {
  cardId: string;
  term: string;
  definition: string;
  grade: number;
  correct: boolean;
  ms: number;
  audioUrl?: string;
  lang?: string;
  phonetic?: string;
}

interface SessionSummaryProps {
  results: SessionResult[];
  durationMs: number;
  stats: StudyStats | null;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  /** Ôn lại ngay các từ trả lời sai/khó trong phiên vừa rồi (không cần tải lại từ máy chủ). */
  onRetryWeak: () => void;
  /** Làm mới hàng đợi và bắt đầu phiên kế tiếp. */
  onNextSession: () => void;
  onBack: () => void;
}

/** Đồng hồ "m:ss" cho ô thời gian (ngắn gọn hơn "1 phút 5 giây" nên vừa ô số liệu). */
export const formatClock = (ms: number): string => {
  const totalSeconds = Math.max(1, Math.round(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
};

export const SessionSummary: React.FC<SessionSummaryProps> = ({
  results,
  durationMs,
  stats,
  onPlayAudio,
  onRetryWeak,
  onNextSession,
  onBack
}) => {
  const total = results.length;
  const correctCount = results.filter((r) => r.correct).length;
  const accuracy = total > 0 ? Math.round((correctCount / total) * 100) : 0;
  const weak = results.filter((r) => !r.correct || r.grade <= 2);
  const uniqueWeak = weak.filter((r, i) => weak.findIndex((x) => x.cardId === r.cardId) === i);
  const headline = accuracy >= 90 ? "Xuất sắc!" : accuracy >= 70 ? "Làm tốt lắm!" : "Cố gắng thêm nhé!";

  return (
    <FcCard padding="none" className="mx-auto w-full max-w-2xl overflow-hidden">
      {/* Banner kết quả: cùng ngôn ngữ thiết kế với banner Dashboard */}
      <div className="relative overflow-hidden bg-gradient-to-r from-[#152a6e] via-[#1e3a8a] to-[#2563eb] px-6 py-7 text-center text-white">
        <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-blue-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-12 left-1/4 h-32 w-32 rounded-full bg-orange-500/20 blur-2xl" />
        <div className="relative z-10 flex flex-col items-center gap-2">
          <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-500 text-white shadow-lg shadow-orange-500/30" aria-hidden="true">
            <Trophy size={32} />
          </span>
          <h3 className="text-2xl font-extrabold tracking-tight">{headline}</h3>
          <p className="text-sm text-blue-100/90">Bạn đã hoàn thành phiên ôn tập.</p>
        </div>
      </div>

      <div className="flex flex-col gap-5 p-6 sm:p-8">
        <div className="grid grid-cols-3 gap-3">
          <FcStat label="thẻ đã ôn" value={total} tone="blue" icon={<Sparkles size={18} />} />
          <FcStat label="chính xác" value={`${accuracy}%`} tone="emerald" icon={<Target size={18} />} />
          <FcStat label="thời gian" value={formatClock(durationMs)} tone="violet" icon={<Clock size={18} />} />
        </div>

        {stats && stats.total > 0 && (
          <div>
            <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
              <span>Tiến độ ghi nhớ của sổ thẻ</span>
              <span>
                {stats.mastered}/{stats.total} đã thuộc
              </span>
            </div>
            <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
              <div className="bg-emerald-500" style={{ width: `${(stats.mastered / stats.total) * 100}%` }} />
              <div className="bg-blue-400" style={{ width: `${(stats.learning / stats.total) * 100}%` }} />
            </div>
          </div>
        )}

        {uniqueWeak.length > 0 ? (
          <div>
            <h4 className="mb-2 text-sm font-bold text-slate-700 dark:text-slate-200">Từ cần chú ý ({uniqueWeak.length})</h4>
            <ul className="flex max-h-52 flex-col gap-2 overflow-y-auto">
              {uniqueWeak.map((w) => (
                <li
                  key={w.cardId}
                  className="flex items-center gap-3 rounded-xl border border-rose-100 bg-rose-50/60 px-3 py-2 dark:border-rose-900/50 dark:bg-rose-950/30"
                >
                  <button
                    type="button"
                    onClick={() => onPlayAudio(w.audioUrl, w.term, w.lang, w.phonetic)}
                    aria-label={`Nghe từ ${w.term}`}
                    className="rounded-full bg-white p-1.5 text-blue-600 shadow-sm transition-colors hover:bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-700 dark:text-blue-300 dark:hover:bg-slate-600"
                  >
                    <Volume2 size={14} aria-hidden="true" />
                  </button>
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{w.term}</span>
                  <span className="flex-1 truncate text-right text-xs text-slate-500 dark:text-slate-400">{w.definition}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="flex items-center justify-center gap-2 rounded-2xl bg-emerald-50 p-3 text-center text-sm font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
            <PartyPopper size={16} aria-hidden="true" />
            Không có từ nào trả lời sai trong phiên này.
          </p>
        )}

        <div className="flex flex-col gap-2 sm:flex-row">
          {uniqueWeak.length > 0 && (
            <FcButton variant="softDanger" onClick={onRetryWeak} icon={<RotateCcw size={15} />} className="flex-1 !rounded-2xl py-3">
              Ôn lại {uniqueWeak.length} từ này ngay
            </FcButton>
          )}
          <FcButton variant="primary" onClick={onNextSession} icon={<Sparkles size={15} />} className="flex-1 !rounded-2xl py-3">
            Học tiếp
          </FcButton>
        </div>
        <FcButton variant="ghost" size="sm" onClick={onBack} icon={<ArrowLeft size={14} />} className="self-center">
          Quay lại Sổ thẻ
        </FcButton>
      </div>
    </FcCard>
  );
};
