import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  Volume2,
  BookOpen,
  Sparkles,
  Keyboard,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  ArrowRight,
  Plus,
  Languages,
  FileSpreadsheet,
  ListChecks,
  Headphones,
  Zap,
  PartyPopper,
  Lightbulb
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import type {
  BackendDeck,
  BackendCardItem,
  StudyModeKind,
  StudyStats,
  VerifySpellingResult
} from "../../services/flashcardService";
import { useFlashcardShortcuts } from "../../hooks/flashcards/useFlashcardShortcuts";
import { ChoiceQuestion } from "./ChoiceQuestion";
import { SessionSummary, type SessionResult } from "./SessionSummary";
import { FcBadge, FcButton, FcCard, FcEmpty } from "./ui";

interface StudyModeProps {
  deck: BackendDeck;
  /** Hàng đợi của phiên học này (được chụp lại khi vào phiên; đổi phiên thì remount bằng `key`). */
  studyQueue: BackendCardItem[];
  stats: StudyStats | null;
  onRateFSRS: (cardId: string, grade: number) => Promise<void>;
  onVerifySpelling: (params: {
    cardId: string;
    userInput: string;
    term: string;
    fallbackPhonetic?: string;
    fallbackExample?: string;
    fallbackAudio?: string;
    langCode?: string;
  }) => Promise<VerifySpellingResult>;
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string, phonetic?: string) => void;
  onPrefetchAudio: (text?: string, lang?: string, phonetic?: string) => void;
  isPlayingAudio: boolean;
  onOpenAddCard: () => void;
  onOpenImportExcel?: () => void;
  onOpenGenerate?: () => void;
  onBackToDecks: () => void;
  /** Tải các từ hay quên của deck để ôn riêng (trả về số thẻ). */
  onStudyWeak?: () => Promise<number>;
  /** Làm mới hàng đợi từ máy chủ và bắt đầu phiên kế tiếp. */
  onNextSession: () => void | Promise<void>;
  /** Gọi khi vừa hoàn thành phiên (để cập nhật thống kê tiến độ). */
  onSessionFinished?: () => void;
}

type ModePreference = "smart" | StudyModeKind;

const MODE_LABELS: Record<StudyModeKind, string> = {
  flip: "Lật thẻ ghi nhớ",
  spelling: "Thử thách Gõ từ",
  choice: "Trắc nghiệm nghĩa",
  listening: "Thử thách nghe"
};

/** Nút chấm điểm FSRS: màu theo mức độ nhớ, kèm phím tắt dạng keycap. */
const RATINGS = [
  {
    grade: 1,
    label: "Quên",
    cls: "border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300 dark:hover:bg-rose-950/70",
    key: "bg-rose-100 text-rose-700 dark:bg-rose-900/60 dark:text-rose-200"
  },
  {
    grade: 2,
    label: "Khó",
    cls: "border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300 dark:hover:bg-amber-950/70",
    key: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200"
  },
  {
    grade: 3,
    label: "Tốt",
    cls: "border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 dark:border-brand-900/60 dark:bg-brand-950/40 dark:text-brand-300 dark:hover:bg-brand-950/70",
    key: "bg-brand-100 text-brand-700 dark:bg-brand-900/60 dark:text-brand-200"
  },
  {
    grade: 4,
    label: "Dễ",
    cls: "border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300 dark:hover:bg-emerald-950/70",
    key: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-200"
  }
];

const shuffle = <T,>(items: T[]): T[] => {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
};

/** Đáp án nhiễu dựng ở client khi thẻ không có `choices` từ máy chủ (deck cục bộ/ngoại tuyến). */
const buildLocalChoices = (card: BackendCardItem, pool: BackendCardItem[]): string[] | null => {
  const answer = card.definition.trim().toLowerCase();
  const others = Array.from(
    new Set(
      pool
        .filter((c) => c.id !== card.id && c.definition.trim() && c.definition.trim().toLowerCase() !== answer)
        .map((c) => c.definition.trim())
    )
  );
  if (others.length < 3) return null;
  return shuffle([...shuffle(others).slice(0, 3), card.definition]);
};

export const StudyMode: React.FC<StudyModeProps> = ({
  deck,
  studyQueue,
  stats,
  onRateFSRS,
  onVerifySpelling,
  onPlayAudio,
  onPrefetchAudio,
  isPlayingAudio,
  onOpenAddCard,
  onOpenImportExcel,
  onOpenGenerate,
  onBackToDecks,
  onStudyWeak,
  onNextSession,
  onSessionFinished
}) => {
  const navigate = useNavigate();

  // --- Trạng thái phiên học ---
  const [sessionQueue, setSessionQueue] = useState<BackendCardItem[]>(studyQueue);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [results, setResults] = useState<SessionResult[]>([]);
  const [finished, setFinished] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const sessionStartedAt = useRef(Date.now());
  const cardShownAt = useRef(Date.now());
  const [sessionDuration, setSessionDuration] = useState(0);

  const [isFlipped, setIsFlipped] = useState(false);
  const [studyModePreference, setStudyModePreference] = useState<ModePreference>("smart");

  // Spelling Challenge State
  const [spellingInput, setSpellingInput] = useState("");
  const [spellingResult, setSpellingResult] = useState<VerifySpellingResult | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const spellingInputRef = useRef<HTMLInputElement | null>(null);

  const currentCard: BackendCardItem | undefined = sessionQueue[currentIndex];
  const deckLang = deck.lang_code || deck.langCode || "en";
  const cardLang = currentCard?.lang_code || currentCard?.langCode || deckLang;

  const choices = useMemo(() => {
    if (!currentCard) return null;
    if (currentCard.choices && currentCard.choices.length >= 4) return currentCard.choices;
    return buildLocalChoices(currentCard, sessionQueue);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentCard?.id]);

  // Chế độ thực tế của thẻ hiện tại (hạ về lật thẻ nếu thiếu dữ liệu cho chế độ được chọn).
  const effectiveMode: StudyModeKind = useMemo(() => {
    if (!currentCard) return "flip";
    const wanted: StudyModeKind =
      studyModePreference === "smart" ? currentCard.recommended_mode || "flip" : studyModePreference;
    if ((wanted === "choice" || wanted === "listening") && !choices) return "flip";
    if (wanted === "spelling" && currentCard.term.trim().split(/\s+/).length > 3 && studyModePreference === "smart") {
      return "flip";
    }
    return wanted;
  }, [currentCard, studyModePreference, choices]);

  // Prefetch current & next audio
  useEffect(() => {
    if (currentCard?.term) {
      onPrefetchAudio(currentCard.term, cardLang);
      const nextCard = sessionQueue[currentIndex + 1];
      if (nextCard?.term) {
        const nextLang = nextCard.lang_code || nextCard.langCode || deckLang;
        onPrefetchAudio(nextCard.term, nextLang);
      }
    }
  }, [currentIndex, currentCard, sessionQueue, deckLang, cardLang, onPrefetchAudio]);

  // Đếm giờ cho từng thẻ
  useEffect(() => {
    cardShownAt.current = Date.now();
  }, [currentIndex, sessionQueue]);

  const resetCardState = () => {
    setIsFlipped(false);
    setSpellingInput("");
    setSpellingResult(null);
  };

  const advanceOrFinish = (nextResults: SessionResult[]) => {
    resetCardState();
    if (currentIndex + 1 < sessionQueue.length) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setSessionDuration(Date.now() - sessionStartedAt.current);
      setFinished(true);
      onSessionFinished?.();
    }
    setResults(nextResults);
  };

  /** Ghi điểm FSRS cho thẻ hiện tại rồi sang thẻ kế tiếp (hoặc kết thúc phiên). */
  const handleRate = async (grade: number, correctOverride?: boolean) => {
    if (!currentCard || isSubmitting) return;
    setIsSubmitting(true);
    const result: SessionResult = {
      cardId: currentCard.id,
      term: currentCard.term,
      definition: currentCard.definition,
      grade,
      correct: correctOverride ?? grade >= 3,
      ms: Date.now() - cardShownAt.current,
      audioUrl: currentCard.audio_url,
      lang: cardLang,
      phonetic: currentCard.phonetic
    };
    try {
      await onRateFSRS(currentCard.id, grade);
    } finally {
      setIsSubmitting(false);
    }
    advanceOrFinish([...results, result]);
  };

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!currentCard || !spellingInput.trim()) return;

    setIsVerifying(true);
    try {
      const res = await onVerifySpelling({
        cardId: currentCard.id,
        userInput: spellingInput.trim(),
        term: currentCard.term,
        fallbackPhonetic: currentCard.phonetic,
        fallbackExample: currentCard.example_sentence || currentCard.example,
        fallbackAudio: currentCard.audio_url,
        langCode: cardLang
      });

      setSpellingResult(res);
      if (res.is_correct) {
        onPlayAudio(res.audio_url || currentCard.audio_url, currentCard.term, cardLang, currentCard.phonetic);
      }
    } catch (err) {
      console.warn("verify error:", err);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleReplayCurrentAudio = () => {
    if (currentCard) {
      onPlayAudio(currentCard.audio_url, currentCard.term, cardLang, currentCard.phonetic);
    }
  };

  const startQueue = (queue: BackendCardItem[]) => {
    setSessionQueue(queue);
    setCurrentIndex(0);
    setResults([]);
    setFinished(false);
    resetCardState();
    sessionStartedAt.current = Date.now();
    cardShownAt.current = Date.now();
  };

  const handleRetryWeak = () => {
    const weakIds = new Set(results.filter((r) => !r.correct || r.grade <= 2).map((r) => r.cardId));
    startQueue(sessionQueue.filter((c) => weakIds.has(c.id)));
  };

  const runBusy = async (action: () => void | Promise<void>) => {
    setIsBusy(true);
    try {
      await action();
    } finally {
      setIsBusy(false);
    }
  };

  // Keyboard Shortcuts hook
  useFlashcardShortcuts({
    enabled: !finished,
    isFlipped: effectiveMode === "flip" && isFlipped,
    hasSpellingResult: effectiveMode === "spelling" && spellingResult !== null,
    onFlip: () => {
      if (effectiveMode === "flip") {
        setIsFlipped((f) => !f);
      }
    },
    onRate: (grade) => void handleRate(grade),
    onReplayAudio: handleReplayCurrentAudio,
    onBack: onBackToDecks
  });

  // ===== Deck chưa có thẻ =====
  if (sessionQueue.length === 0 && (!stats || stats.total === 0)) {
    return (
      <FcEmpty
        className="min-h-[350px]"
        icon={<BookOpen size={30} />}
        title="Sổ thẻ này chưa có từ vựng nào"
        description="Bạn có thể nhờ AI tạo từ vựng theo chủ đề, thêm từ mới tại đây hoặc dùng tính năng Dịch tài liệu để AI tự động trích xuất bảng từ vựng vào sổ này."
      >
        {onOpenGenerate && (
          <FcButton variant="primary" onClick={onOpenGenerate} icon={<Zap size={16} />}>
            Tạo từ vựng bằng AI
          </FcButton>
        )}
        <FcButton variant="secondary" onClick={onOpenAddCard} icon={<Plus size={16} />}>
          Thêm thẻ mới
        </FcButton>
        {onOpenImportExcel && (
          <FcButton variant="success" onClick={onOpenImportExcel} icon={<FileSpreadsheet size={16} />}>
            Nhập từ Excel / CSV
          </FcButton>
        )}
        <FcButton variant="secondary" onClick={() => navigate("/translation")} icon={<Languages size={16} />}>
          Đến Trang Dịch thuật
        </FcButton>
      </FcEmpty>
    );
  }

  // ===== Hôm nay không còn thẻ cần ôn =====
  if (sessionQueue.length === 0) {
    return (
      <FcEmpty
        className="min-h-[350px]"
        icon={<PartyPopper size={30} className="text-amber-500" />}
        title="Hôm nay bạn đã ôn xong!"
        description={
          <>
            Không còn thẻ nào đến hạn. Hãy quay lại sau, hoặc thêm từ mới để học tiếp.
            {stats && (
              <span className="mt-3 block text-xs font-semibold text-slate-600 dark:text-slate-300">
                Đã thuộc {stats.mastered}/{stats.total} · Đang học {stats.learning}
              </span>
            )}
          </>
        }
      >
        {onStudyWeak && stats && stats.weak > 0 && (
          <FcButton
            variant="softDanger"
            loading={isBusy}
            onClick={() => runBusy(async () => void (await onStudyWeak()))}
            icon={<RefreshCw size={15} />}
          >
            Ôn {stats.weak} từ hay quên
          </FcButton>
        )}
        {onOpenGenerate && (
          <FcButton variant="primary" onClick={onOpenGenerate} icon={<Zap size={16} />}>
            Thêm từ mới bằng AI
          </FcButton>
        )}
      </FcEmpty>
    );
  }

  // ===== Tổng kết phiên =====
  if (finished) {
    return (
      <SessionSummary
        results={results}
        durationMs={sessionDuration}
        stats={stats}
        onPlayAudio={onPlayAudio}
        onRetryWeak={handleRetryWeak}
        onNextSession={() => void runBusy(onNextSession)}
        onBack={onBackToDecks}
      />
    );
  }

  const modeButtons: { key: ModePreference; label: string; icon: React.ReactNode }[] = [
    { key: "smart", label: "Tự động", icon: <Sparkles size={14} aria-hidden="true" /> },
    { key: "flip", label: "Lật thẻ", icon: <Layers size={14} aria-hidden="true" /> },
    { key: "choice", label: "Trắc nghiệm", icon: <ListChecks size={14} aria-hidden="true" /> },
    { key: "listening", label: "Nghe", icon: <Headphones size={14} aria-hidden="true" /> },
    { key: "spelling", label: "Gõ từ", icon: <Keyboard size={14} aria-hidden="true" /> }
  ];

  const progressPct = ((currentIndex + 1) / sessionQueue.length) * 100;

  return (
    <div className="flex w-full flex-col gap-4">
      {/* Tiến độ ghi nhớ của sổ thẻ */}
      {stats && stats.total > 0 && (
        <div className="mx-auto flex w-full max-w-2xl flex-wrap items-center justify-center gap-2">
          <FcBadge tone="sky">Mới {stats.new}</FcBadge>
          <FcBadge tone="orange">Đến hạn {stats.due}</FcBadge>
          <FcBadge tone="blue">Đang học {stats.learning}</FcBadge>
          <FcBadge tone="emerald">Đã thuộc {stats.mastered}</FcBadge>
        </div>
      )}

      {/* Chọn chế độ ôn tập */}
      <div
        role="group"
        aria-label="Chế độ ôn tập"
        className="mx-auto flex w-full max-w-xl flex-wrap items-center justify-center gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-900"
      >
        {modeButtons.map((m) => {
          const active = studyModePreference === m.key;
          return (
            <button
              key={m.key}
              type="button"
              aria-pressed={active}
              onClick={() => {
                setStudyModePreference(m.key);
                resetCardState();
              }}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 [@media(pointer:coarse)]:min-h-[44px] text-xs font-semibold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                active
                  ? "bg-white text-brand-600 shadow-sm dark:bg-slate-700 dark:text-brand-300"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              {m.icon}
              <span>{m.label}</span>
            </button>
          );
        })}
      </div>

      {/* Khu vực thẻ chính */}
      <div className="mx-auto flex w-full max-w-2xl flex-col items-center justify-center gap-4">
        {/* Thanh tiến độ phiên */}
        <div className="w-full">
          <div className="mb-1.5 flex justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full bg-brand-600" aria-hidden="true"></span>
              Đang ôn tập: {MODE_LABELS[effectiveMode]}
            </span>
            <span>
              Thẻ {currentIndex + 1} / {sessionQueue.length}
            </span>
          </div>
          <div
            role="progressbar"
            aria-label="Tiến độ phiên ôn tập"
            aria-valuemin={0}
            aria-valuemax={sessionQueue.length}
            aria-valuenow={currentIndex + 1}
            className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"
          >
            <div className="h-full rounded-full bg-brand-600 transition-all duration-300" style={{ width: `${progressPct}%` }}></div>
          </div>
        </div>

        {/* MODE: CHOICE / LISTENING */}
        {(effectiveMode === "choice" || effectiveMode === "listening") && currentCard && choices ? (
          <ChoiceQuestion
            key={`${currentCard.id}-${effectiveMode}`}
            card={currentCard}
            choices={choices}
            variant={effectiveMode}
            isPlayingAudio={isPlayingAudio}
            onPlay={handleReplayCurrentAudio}
            onFinish={(correct) => void handleRate(correct ? 3 : 1, correct)}
          />
        ) : effectiveMode === "spelling" && currentCard ? (
          /* MODE: SPELLING */
          <FcCard padding="lg" className="w-full">
            <div className="mb-4 flex items-center justify-between gap-2">
              <FcBadge tone="amber" icon={<Keyboard size={13} aria-hidden="true" />}>
                Thử thách Gõ chính tả
              </FcBadge>
              <FcButton
                variant="soft"
                size="sm"
                onClick={handleReplayCurrentAudio}
                title="Phím tắt: R"
                icon={<Volume2 size={14} className={isPlayingAudio ? "animate-pulse" : ""} />}
              >
                Nghe phát âm (R)
              </FcButton>
            </div>

            <div className="my-6 text-center">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Nghĩa Tiếng Việt</span>
              <h3 className="mt-1 text-2xl font-bold text-slate-800 dark:text-slate-100">{currentCard.definition}</h3>
              {currentCard.cloze_sentence || currentCard.example_sentence ? (
                <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm italic text-slate-700 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-300">
                  "{currentCard.cloze_sentence || currentCard.example_sentence}"
                </div>
              ) : null}
            </div>

            <form onSubmit={handleVerify} className="mt-6 flex flex-col gap-3">
              <input
                ref={spellingInputRef}
                type="text"
                value={spellingInput}
                onChange={(e) => setSpellingInput(e.target.value)}
                placeholder="Gõ từ khóa gốc bằng ngoại ngữ tại đây..."
                aria-label="Từ cần gõ"
                disabled={spellingResult !== null}
                autoFocus
                lang={cardLang}
                className="w-full rounded-2xl border-2 border-slate-200 bg-slate-50/50 px-5 py-4 text-center text-lg font-bold text-slate-800 placeholder-slate-400 transition-all focus:border-brand-500 focus:bg-white focus:outline-none dark:border-slate-600 dark:bg-slate-900/50 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:border-brand-400 dark:focus:bg-slate-900"
              />

              {!spellingResult ? (
                <div className="flex gap-2">
                  <FcButton
                    type="submit"
                    variant="primary"
                    loading={isVerifying}
                    disabled={!spellingInput.trim()}
                    icon={!isVerifying ? <Send size={16} /> : undefined}
                    className="flex-1 !rounded-2xl py-3.5"
                  >
                    Kiểm tra chính tả (Enter)
                  </FcButton>
                  <FcButton
                    variant="secondary"
                    onClick={() => {
                      setSpellingInput(currentCard.term);
                      handleVerify();
                    }}
                    className="!rounded-2xl"
                  >
                    Xem đáp án
                  </FcButton>
                </div>
              ) : (
                <div className="mt-2 flex animate-in flex-col gap-4 fade-in duration-200">
                  <div
                    role="status"
                    className={`rounded-2xl border p-4 text-center ${
                      spellingResult.is_correct
                        ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200"
                        : spellingResult.is_close
                        ? "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200"
                        : "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200"
                    }`}
                  >
                    <div className="mb-1 flex items-center justify-center gap-2 text-base font-bold">
                      {spellingResult.is_correct ? (
                        <CheckCircle2 size={20} className="text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                      ) : (
                        <AlertCircle size={20} className="text-rose-600 dark:text-rose-400" aria-hidden="true" />
                      )}
                      <span>{spellingResult.feedback}</span>
                    </div>
                    {currentCard.phonetic ? (
                      <span className="font-mono text-xs text-slate-500 dark:text-slate-400">Phiên âm: {currentCard.phonetic}</span>
                    ) : null}
                  </div>

                  <FcButton
                    variant="primary"
                    disabled={isSubmitting}
                    onClick={() => void handleRate(spellingResult.suggested_grade)}
                    className="w-full !rounded-2xl py-3.5"
                  >
                    <span>Tiếp tục sang thẻ kế tiếp (Phím 1-4 hoặc Click)</span>
                    <ArrowRight size={16} aria-hidden="true" />
                  </FcButton>
                </div>
              )}
            </form>
          </FcCard>
        ) : (
          /* MODE: FLIP CARD */
          currentCard && (
            <div className="flex w-full flex-col items-center gap-6">
              <div style={{ perspective: "1200px" }} className="w-full">
                <FcCard
                  padding="lg"
                  interactive
                  onClick={() => setIsFlipped((f) => !f)}
                  className={`relative min-h-[260px] w-full cursor-pointer ${isFlipped ? "!bg-slate-50 dark:!bg-slate-800/80" : ""}`}
                >
                  <div className="absolute right-5 top-5 flex items-center gap-2">
                    {currentCard.is_new && <FcBadge tone="sky" className="uppercase">Từ mới</FcBadge>}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleReplayCurrentAudio();
                      }}
                      className="rounded-full bg-brand-50 p-2.5 [@media(pointer:coarse)]:p-3 text-brand-600 transition-colors hover:bg-brand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:bg-slate-700 dark:text-brand-300 dark:hover:bg-slate-600"
                      title="Nghe phát âm (Phím R)"
                      aria-label="Nghe phát âm"
                    >
                      <Volume2 size={18} className={isPlayingAudio ? "animate-pulse" : ""} aria-hidden="true" />
                    </button>
                  </div>

                  {/* key đổi theo mặt thẻ để chạy lại hiệu ứng lật (tắt khi người dùng chọn giảm chuyển động) */}
                  {!isFlipped ? (
                    <div key="front" className="flex min-h-[200px] animate-flip-in pt-10 sm:pt-0 flex-col items-center justify-center text-center motion-reduce:animate-none">
                      <FcBadge tone="slate" className="uppercase tracking-wider">
                        {currentCard.part_of_speech || "Từ vựng"}
                      </FcBadge>
                      <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 sm:text-4xl" lang={cardLang}>
                        {currentCard.term}
                      </h2>
                      {currentCard.phonetic ? (
                        <p className="mt-2 font-mono text-sm text-brand-600 dark:text-brand-300">{currentCard.phonetic}</p>
                      ) : null}
                      <p className="mt-8 flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
                        <Lightbulb size={14} aria-hidden="true" />
                        Bấm vào thẻ (hoặc nhấn Space) để lật xem định nghĩa
                      </p>
                    </div>
                  ) : (
                    <div key="back" className="flex min-h-[200px] animate-flip-in pt-10 sm:pt-0 flex-col items-center justify-center text-center motion-reduce:animate-none">
                      <FcBadge tone="blue" className="uppercase tracking-wider">
                        Định nghĩa
                      </FcBadge>
                      <h3 className="mt-4 text-2xl font-bold text-slate-800 dark:text-slate-100">{currentCard.definition}</h3>
                      {currentCard.example_sentence || currentCard.example ? (
                        <p className="mt-4 max-w-md rounded-xl border border-slate-200 bg-white p-3 text-sm italic text-slate-600 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-300" lang={cardLang}>
                          "{currentCard.example_sentence || currentCard.example}"
                          {currentCard.example_translation && (
                            <span className="mt-1 block not-italic text-slate-500 dark:text-slate-400" lang="vi">{currentCard.example_translation}</span>
                          )}
                        </p>
                      ) : null}
                    </div>
                  )}
                </FcCard>
              </div>

              {/* Nút chấm điểm FSRS */}
              {isFlipped ? (
                <div className="sticky bottom-3 z-10 flex w-full flex-col items-center gap-2 rounded-2xl bg-brand-50/90 p-2 backdrop-blur dark:bg-slate-950/90">
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                    Đánh giá mức độ ghi nhớ FSRS (Phím tắt: 1, 2, 3, 4):
                  </span>
                  <div className="grid w-full grid-cols-2 gap-2 sm:grid-cols-4">
                    {RATINGS.map((b) => (
                      <button
                        key={b.grade}
                        type="button"
                        disabled={isSubmitting}
                        onClick={() => void handleRate(b.grade)}
                        className={`flex items-center justify-center gap-2 rounded-2xl border py-3 text-sm font-bold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-50 ${b.cls}`}
                        title={`Phím tắt: ${b.grade}`}
                      >
                        <kbd aria-hidden="true" className={`flex h-6 w-6 items-center justify-center rounded-md font-sans text-xs font-extrabold ${b.key}`}>
                          {b.grade}
                        </kbd>
                        <span>{b.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          )
        )}
      </div>
    </div>
  );
};
