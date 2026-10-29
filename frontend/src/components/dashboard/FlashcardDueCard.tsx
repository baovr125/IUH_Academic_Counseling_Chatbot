import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, BookMarked, BookOpen, Flame, Library, LogIn, PartyPopper, RefreshCw, Target, Trophy } from "lucide-react";
import { LANG_CONFIG } from "../../services/deckStorage";
import { useFlashcardOverview, type FlashcardOverview } from "../../hooks/flashcards/useFlashcardOverview";
import { DAILY_GOAL_MAX, DAILY_GOAL_MIN, DAILY_GOAL_PRESETS, useDailyGoal } from "../../hooks/useDailyGoal";
import { FcBadge, FcButton, FcLoading, FcSkeleton, LangFlag } from "../flashcards/ui";

const langName = (code: string) => LANG_CONFIG[code]?.viName ?? code.toUpperCase();
const fmt = (n: number | null | undefined) => (typeof n === "number" ? n.toLocaleString("vi-VN") : "—");

/** Ô số liệu nhỏ trong thẻ: số lớn + nhãn; `null` hiện "—" khi không tải được. */
const MiniStat: React.FC<{ label: string; value: number | null; icon: React.ReactNode; tone: string }> = ({ label, value, icon, tone }) => (
  <div className="min-w-0 rounded-2xl border border-slate-100 bg-slate-50/70 p-2.5 sm:p-3 dark:border-slate-700/60 dark:bg-slate-900/60">
    <span aria-hidden="true" className={`flex h-7 w-7 items-center justify-center rounded-lg ${tone}`}>
      {icon}
    </span>
    <p className="mt-2 text-xl font-extrabold leading-none text-slate-900 dark:text-slate-100">{fmt(value)}</p>
    <p className="mt-1 text-xs font-semibold leading-tight text-slate-500 dark:text-slate-400">{label}</p>
  </div>
);

const GoalSelect: React.FC<{ goal: number; onChange: (n: number) => void }> = ({ goal, onChange }) => {
  const options: number[] = Array.from(new Set<number>([...DAILY_GOAL_PRESETS, goal])).sort((a, b) => a - b);
  return (
    <label className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
      <span>Mục tiêu</span>
      <select
        aria-label={`Mục tiêu số từ ôn mỗi ngày (${DAILY_GOAL_MIN}–${DAILY_GOAL_MAX})`}
        value={goal}
        onChange={(e) => onChange(Number(e.target.value))}
        className="rounded-lg border border-slate-200 bg-white px-2 py-1 [@media(pointer:coarse)]:py-2.5 text-xs font-bold text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200"
      >
        {options.map((n) => (
          <option key={n} value={n}>
            {n} từ/ngày
          </option>
        ))}
      </select>
    </label>
  );
};

const GoalProgress: React.FC<{ reviewed: number | null; goal: number; onGoalChange: (n: number) => void }> = ({ reviewed, goal, onGoalChange }) => {
  const percent = reviewed === null ? 0 : Math.min(100, Math.round((reviewed / goal) * 100));
  const reached = reviewed !== null && reviewed >= goal;
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
          Đã ôn hôm nay: {fmt(reviewed)}/{goal} từ
        </span>
        <GoalSelect goal={goal} onChange={onGoalChange} />
      </div>
      <div
        role="progressbar"
        aria-label="Tiến độ mục tiêu ôn tập hôm nay"
        aria-valuemin={0}
        aria-valuemax={goal}
        aria-valuenow={reviewed ?? 0}
        className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700"
      >
        <div
          className={`h-full rounded-full transition-all duration-500 motion-reduce:transition-none ${reached ? "bg-emerald-500" : "bg-brand-500"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        {reviewed === null ? "Chưa tải được số từ đã ôn hôm nay." : reached ? "Bạn đã đạt mục tiêu hôm nay, tuyệt vời!" : `${percent}% mục tiêu hôm nay`}
      </p>
    </div>
  );
};

const CARD_CLASS =
  "flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-800";

interface BodyProps {
  overview: FlashcardOverview & { refetch: () => void };
  goal: number;
  setGoal: (n: number) => void;
}

/** Nội dung phần giữa của thẻ, thay đổi theo trạng thái dữ liệu. */
const CardBody: React.FC<BodyProps> = ({ overview, goal, setGoal }) => {
  const { status } = overview;

  if (status === "loading") {
    return (
      <FcLoading label="Đang tải số liệu Flashcard…" className="mt-5 space-y-4">
        <FcSkeleton className="h-3 w-40" />
        <FcSkeleton className="h-2.5 w-full" />
        <div className="grid grid-cols-3 gap-2">
          {[0, 1, 2].map((i) => (
            <FcSkeleton key={i} className="h-[88px] rounded-2xl" />
          ))}
        </div>
      </FcLoading>
    );
  }

  if (status === "guest") {
    return (
      <p className="mt-5 text-sm text-slate-600 dark:text-slate-300">
        Đăng nhập để xem số từ cần ôn, tiến độ mục tiêu hôm nay và chuỗi ngày học của bạn.
      </p>
    );
  }

  if (status === "error") {
    return (
      <div className="mt-5 space-y-3">
        <div className="grid grid-cols-3 gap-2" data-testid="flashcard-stats">
          <MiniStat label="Cần ôn" value={null} icon={<Target size={15} />} tone="bg-orange-50 text-orange-600 dark:bg-orange-950/50 dark:text-orange-300" />
          <MiniStat label="Đã thuộc" value={null} icon={<Trophy size={15} />} tone="bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-300" />
          <MiniStat label="Tổng số từ" value={null} icon={<BookOpen size={15} />} tone="bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-300" />
        </div>
        <p role="alert" className="text-xs text-rose-700 dark:text-rose-300">
          Không tải được số liệu Flashcard. Các phần khác của Dashboard vẫn hoạt động bình thường.
        </p>
      </div>
    );
  }

  if (status === "empty") {
    return (
      <div className="mt-5 rounded-2xl border border-dashed border-slate-300 p-4 text-center dark:border-slate-600">
        <p className="text-sm font-bold text-slate-800 dark:text-slate-100">Bạn chưa có thẻ từ vựng nào</p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Tạo sổ thẻ đầu tiên, nhập từ hoặc để AI sinh từ vựng theo chủ đề, rồi quay lại đây để ôn tập.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-5 space-y-4">
      <GoalProgress reviewed={overview.reviewedToday} goal={goal} onGoalChange={setGoal} />
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-2" data-testid="flashcard-stats">
          <MiniStat label="Cần ôn" value={overview.due} icon={<Target size={15} />} tone="bg-orange-50 text-orange-600 dark:bg-orange-950/50 dark:text-orange-300" />
          <MiniStat label="Đã thuộc" value={overview.mastered} icon={<Trophy size={15} />} tone="bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-300" />
          <MiniStat label="Tổng số từ" value={overview.totalCards} icon={<BookOpen size={15} />} tone="bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-300" />
        </div>
        {status === "ready" && overview.topDueLang && (
          <p className="flex min-w-0 items-center gap-2 text-xs text-slate-500 dark:text-slate-400" data-testid="top-language">
            <LangFlag lang={overview.topDueLang.code} size="sm" />
            <span className="truncate">
              Ưu tiên: <span className="font-semibold text-slate-700 dark:text-slate-200">{langName(overview.topDueLang.code)}</span> ({overview.topDueLang.due} từ đến hạn)
            </span>
          </p>
        )}
        {status === "all_done" && (
          <p className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300" data-testid="all-done">
            <PartyPopper size={15} aria-hidden="true" /> Hôm nay bạn đã ôn xong, hãy quay lại vào ngày mai.
          </p>
        )}
      </div>
    </div>
  );
};

/** Thẻ "Ôn tập Thẻ Từ vựng FSRS" của Dashboard: số liệu thật từ service Flashcard, đủ trạng thái tải/lỗi/trống. */
export const FlashcardDueCard: React.FC = () => {
  const navigate = useNavigate();
  const overview = useFlashcardOverview();
  const { goal, setGoal } = useDailyGoal();
  const { status, topDueLang, topNewLang } = overview;

  const badge = (() => {
    if (status === "ready") return <FcBadge tone="orange" className="shrink-0 whitespace-nowrap" icon={<Flame size={13} aria-hidden="true" />}>{overview.due} từ cần ôn</FcBadge>;
    if (status === "all_done") return <FcBadge tone="emerald" className="shrink-0 whitespace-nowrap" icon={<PartyPopper size={13} aria-hidden="true" />}>Đã ôn xong</FcBadge>;
    if (status === "loading") return <FcSkeleton className="h-6 w-24 rounded-full" />;
    return null;
  })();

  let cta: React.ReactNode;
  if (status === "ready" && topDueLang) {
    cta = (
      <button
        type="button"
        onClick={() => navigate(`/flashcards/${topDueLang.code}`)}
        className={`group flex w-full items-center justify-center gap-2.5 rounded-2xl bg-brand-600 px-4 py-3 text-sm font-bold text-white shadow-md shadow-brand-600/20 transition-all hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-800`}
      >
        <LangFlag lang={topDueLang.code} size="sm" />
        <span>
          Bắt đầu Ôn tập Ngay · {langName(topDueLang.code)} ({topDueLang.due} từ)
        </span>
        <ArrowRight size={16} aria-hidden="true" className="transition-transform group-hover:translate-x-1 motion-reduce:transition-none" />
      </button>
    );
  } else if (status === "all_done" && topNewLang) {
    cta = (
      <FcButton variant="primary" className="w-full" onClick={() => navigate(`/flashcards/${topNewLang.code}`)}>
        <LangFlag lang={topNewLang.code} size="sm" />
        Học thêm từ mới · {langName(topNewLang.code)} ({topNewLang.count})
      </FcButton>
    );
  } else if (status === "all_done") {
    cta = (
      <FcButton variant="secondary" className="w-full" icon={<Library size={16} />} onClick={() => navigate("/flashcards")}>
        Xem sổ thẻ của tôi
      </FcButton>
    );
  } else if (status === "empty") {
    cta = (
      <FcButton variant="primary" className="w-full" icon={<BookOpen size={16} />} onClick={() => navigate("/flashcards")}>
        Tạo sổ thẻ đầu tiên
      </FcButton>
    );
  } else if (status === "guest") {
    cta = (
      <FcButton variant="primary" className="w-full" icon={<LogIn size={16} />} onClick={() => navigate("/login")}>
        Đăng nhập
      </FcButton>
    );
  } else if (status === "error") {
    cta = (
      <FcButton variant="secondary" className="w-full" icon={<RefreshCw size={16} />} onClick={overview.refetch}>
        Thử lại
      </FcButton>
    );
  } else {
    cta = <FcSkeleton className="h-11 w-full rounded-2xl" />;
  }

  return (
    <section aria-label="Ôn tập thẻ từ vựng" className={CARD_CLASS} data-testid="flashcard-due-card" data-status={status}>
      <div>
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-brand-100 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300">
              <BookMarked size={20} aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Ôn tập Thẻ Từ vựng FSRS</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Ghi nhớ ngắt quãng thông minh</p>
            </div>
          </div>
          {badge}
        </div>
        <CardBody overview={overview} goal={goal} setGoal={setGoal} />
      </div>
      <div className="mt-6 border-t border-slate-100 pt-4 dark:border-slate-700/60">{cta}</div>
    </section>
  );
};
