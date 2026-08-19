import React, { useState, useEffect, useRef } from "react";
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
  ArrowLeft,
  Plus,
  Languages,
  FileSpreadsheet
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { BackendDeck, BackendCardItem, VerifySpellingResult } from "../../services/flashcardService";
import { useFlashcardShortcuts } from "../../hooks/flashcards/useFlashcardShortcuts";

interface StudyModeProps {
  deck: BackendDeck;
  studyQueue: BackendCardItem[];
  isLoading: boolean;
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
  onPlayAudio: (audioUrl?: string, text?: string, lang?: string) => void;
  onPrefetchAudio: (text?: string, lang?: string) => void;
  isPlayingAudio: boolean;
  onOpenAddCard: () => void;
  onOpenImportExcel?: () => void;
  onBackToDecks: () => void;
}

export const StudyMode: React.FC<StudyModeProps> = ({
  deck,
  studyQueue,
  isLoading,
  onRateFSRS,
  onVerifySpelling,
  onPlayAudio,
  onPrefetchAudio,
  isPlayingAudio,
  onOpenAddCard,
  onOpenImportExcel,
  onBackToDecks
}) => {
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [studyModePreference, setStudyModePreference] = useState<"smart" | "flip" | "spelling">("smart");

  // Spelling Challenge State
  const [spellingInput, setSpellingInput] = useState("");
  const [spellingResult, setSpellingResult] = useState<VerifySpellingResult | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const spellingInputRef = useRef<HTMLInputElement | null>(null);

  const currentCard: BackendCardItem | undefined = studyQueue[currentIndex];
  const deckLang = deck.lang_code || deck.langCode || "en";
  const cardLang = currentCard?.lang_code || currentCard?.langCode || deckLang;

  // Prefetch current & next audio
  useEffect(() => {
    if (currentCard?.term) {
      onPrefetchAudio(currentCard.term, cardLang);
      const nextCard = studyQueue[currentIndex + 1];
      if (nextCard?.term) {
        const nextLang = nextCard.lang_code || nextCard.langCode || deckLang;
        onPrefetchAudio(nextCard.term, nextLang);
      }
    }
  }, [currentIndex, currentCard, studyQueue, deckLang, cardLang, onPrefetchAudio]);

  // Determine effective mode for current card
  const effectiveMode =
    studyModePreference === "smart"
      ? currentCard?.recommended_mode || "flip"
      : studyModePreference;

  const advanceToNextCard = () => {
    setIsFlipped(false);
    setSpellingInput("");
    setSpellingResult(null);
    if (currentIndex + 1 < studyQueue.length) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setCurrentIndex(0);
    }
  };

  const handleRate = async (grade: number) => {
    if (!currentCard) return;
    await onRateFSRS(currentCard.id, grade);
    advanceToNextCard();
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
        onPlayAudio(res.audio_url || currentCard.audio_url, currentCard.term, cardLang);
      }
    } catch (err) {
      console.warn("verify error:", err);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleReplayCurrentAudio = () => {
    if (currentCard) {
      onPlayAudio(currentCard.audio_url, currentCard.term, cardLang);
    }
  };

  // Keyboard Shortcuts hook
  useFlashcardShortcuts({
    enabled: true,
    isFlipped,
    hasSpellingResult: spellingResult !== null,
    onFlip: () => {
      if (effectiveMode === "flip") {
        setIsFlipped((f) => !f);
      }
    },
    onRate: handleRate,
    onReplayAudio: handleReplayCurrentAudio,
    onBack: onBackToDecks
  });

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[350px]">
        <RefreshCw size={32} className="animate-spin text-blue-600" />
      </div>
    );
  }

  if (studyQueue.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm min-h-[350px]">
        <BookOpen size={48} className="mb-3 text-slate-300" />
        <h3 className="text-base font-bold text-slate-700">Sổ thẻ này chưa có từ vựng nào</h3>
        <p className="mt-1 max-w-sm text-xs text-slate-500">
          Bạn có thể thêm từ mới ngay tại đây hoặc sử dụng tính năng Dịch tài liệu để AI tự động trích xuất bảng từ vựng vào sổ này.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={onOpenAddCard}
            className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
          >
            <Plus size={15} />
            <span>Thêm thẻ mới ngay</span>
          </button>
          {onOpenImportExcel && (
            <button
              type="button"
              onClick={onOpenImportExcel}
              className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition-colors shadow-sm"
            >
              <FileSpreadsheet size={15} />
              <span>Nhập từ Excel / CSV</span>
            </button>
          )}
          <button
            type="button"
            onClick={() => navigate("/translation")}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <Languages size={15} />
            <span>Đến Trang Dịch thuật</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Mode Selector Pill */}
      <div className="flex items-center justify-center gap-1 rounded-xl bg-slate-100 p-1 text-xs font-semibold text-slate-600 max-w-md mx-auto w-full">
        <button
          type="button"
          onClick={() => setStudyModePreference("smart")}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
            studyModePreference === "smart" ? "bg-white text-blue-600 shadow-sm" : "hover:text-slate-900"
          }`}
        >
          <Sparkles size={14} />
          <span>Tự động (FSRS)</span>
        </button>
        <button
          type="button"
          onClick={() => setStudyModePreference("flip")}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
            studyModePreference === "flip" ? "bg-white text-blue-600 shadow-sm" : "hover:text-slate-900"
          }`}
        >
          <Layers size={14} />
          <span>Lật thẻ</span>
        </button>
        <button
          type="button"
          onClick={() => setStudyModePreference("spelling")}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
            studyModePreference === "spelling" ? "bg-white text-blue-600 shadow-sm" : "hover:text-slate-900"
          }`}
        >
          <Keyboard size={14} />
          <span>Gõ chính tả</span>
        </button>
      </div>

      {/* Main Card Area */}
      <div className="flex flex-col items-center justify-center gap-5 max-w-2xl mx-auto w-full">
        {/* Progress Bar */}
        <div className="w-full">
          <div className="mb-1.5 flex justify-between text-xs font-medium text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full bg-blue-600"></span>
              Đang ôn tập: {effectiveMode === "spelling" ? "Thử thách Gõ từ" : "Lật thẻ ghi nhớ"}
            </span>
            <span>
              Thẻ {currentIndex + 1} / {studyQueue.length}
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${((currentIndex + 1) / studyQueue.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* MODE A: SPELLING */}
        {effectiveMode === "spelling" && currentCard ? (
          <div className="w-full rounded-3xl border border-slate-200/80 bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700 border border-amber-200 flex items-center gap-1">
                <Keyboard size={13} /> Thử thách Gõ chính tả
              </span>
              <button
                type="button"
                onClick={handleReplayCurrentAudio}
                className="flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors"
                title="Phím tắt: R"
              >
                <Volume2 size={14} className={isPlayingAudio ? "animate-pulse text-blue-600" : ""} />
                <span>Nghe phát âm (R)</span>
              </button>
            </div>

            <div className="text-center my-6">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Nghĩa Tiếng Việt</span>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">{currentCard.definition}</h3>
              {currentCard.cloze_sentence || currentCard.example_sentence ? (
                <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700 italic border border-slate-100">
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
                disabled={spellingResult !== null}
                autoFocus
                className="w-full rounded-2xl border-2 border-slate-200 bg-slate-50/50 px-5 py-4 text-center text-lg font-bold text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none transition-all"
              />

              {!spellingResult ? (
                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={isVerifying || !spellingInput.trim()}
                    className="flex-1 flex items-center justify-center gap-2 rounded-2xl bg-blue-600 py-3.5 text-sm font-bold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-all"
                  >
                    {isVerifying ? <RefreshCw size={16} className="animate-spin" /> : <Send size={16} />}
                    <span>Kiểm tra chính tả (Enter)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setSpellingInput(currentCard.term);
                      handleVerify();
                    }}
                    className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    Xem đáp án
                  </button>
                </div>
              ) : (
                <div className="mt-2 flex flex-col gap-4 animate-in fade-in duration-200">
                  <div
                    className={`rounded-2xl p-4 text-center border ${
                      spellingResult.is_correct
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                        : spellingResult.is_close
                        ? "bg-amber-50 text-amber-800 border-amber-200"
                        : "bg-rose-50 text-rose-800 border-rose-200"
                    }`}
                  >
                    <div className="flex items-center justify-center gap-2 font-bold text-base mb-1">
                      {spellingResult.is_correct ? (
                        <CheckCircle2 size={20} className="text-emerald-600" />
                      ) : (
                        <AlertCircle size={20} className="text-rose-600" />
                      )}
                      <span>{spellingResult.feedback}</span>
                    </div>
                    {currentCard.phonetic ? (
                      <span className="text-xs text-slate-500 font-mono">Phiên âm: {currentCard.phonetic}</span>
                    ) : null}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRate(spellingResult.suggested_grade)}
                    className="w-full rounded-2xl bg-blue-600 py-3.5 text-sm font-bold text-white shadow-sm hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
                  >
                    <span>Tiếp tục sang thẻ kế tiếp (Phím 1-4 hoặc Click)</span>
                    <ArrowLeft size={16} className="rotate-180" />
                  </button>
                </div>
              )}
            </form>
          </div>
        ) : (
          /* MODE B: FLIP CARD */
          currentCard && (
            <div className="w-full flex flex-col items-center gap-6">
              <div
                onClick={() => setIsFlipped((f) => !f)}
                className={`relative min-h-[280px] w-full cursor-pointer rounded-3xl border border-slate-200/80 bg-white p-8 shadow-sm transition-all duration-300 hover:shadow-md ${
                  isFlipped ? "bg-slate-50/70" : ""
                }`}
              >
                <div className="absolute right-6 top-6 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReplayCurrentAudio();
                    }}
                    className="rounded-full bg-blue-50 p-2.5 text-blue-600 hover:bg-blue-100 transition-colors"
                    title="Nghe phát âm (Phím R)"
                  >
                    <Volume2 size={18} className={isPlayingAudio ? "animate-pulse" : ""} />
                  </button>
                </div>

                {!isFlipped ? (
                  <div className="flex h-full min-h-[220px] flex-col items-center justify-center text-center">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      {currentCard.part_of_speech || "Từ vựng"}
                    </span>
                    <h2 className="mt-4 text-3xl font-extrabold text-slate-800 tracking-tight">
                      {currentCard.term}
                    </h2>
                    {currentCard.phonetic ? (
                      <p className="mt-2 font-mono text-sm text-blue-600">{currentCard.phonetic}</p>
                    ) : null}
                    <p className="mt-8 text-xs font-semibold text-slate-400">💡 Bấm vào thẻ (hoặc nhấn Space) để lật xem định nghĩa</p>
                  </div>
                ) : (
                  <div className="flex h-full min-h-[220px] flex-col items-center justify-center text-center">
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-[11px] font-bold text-blue-600 uppercase tracking-wider">
                      Định nghĩa
                    </span>
                    <h3 className="mt-4 text-2xl font-bold text-slate-800">{currentCard.definition}</h3>
                    {currentCard.example_sentence || currentCard.example ? (
                      <p className="mt-4 max-w-md text-xs italic text-slate-600 bg-white p-3 rounded-xl border border-slate-100">
                        "{currentCard.example_sentence || currentCard.example}"
                      </p>
                    ) : null}
                  </div>
                )}
              </div>

              {/* FSRS Rating Buttons */}
              {isFlipped ? (
                <div className="flex w-full flex-col items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">
                    Đánh giá mức độ ghi nhớ FSRS (Phím tắt: 1, 2, 3, 4):
                  </span>
                  <div className="grid w-full grid-cols-4 gap-2">
                    <button
                      type="button"
                      onClick={() => handleRate(1)}
                      className="rounded-2xl border border-rose-200 bg-rose-50/70 py-3 text-xs font-bold text-rose-700 hover:bg-rose-100 transition-colors"
                      title="Phím tắt: 1"
                    >
                      🔴 [1] Quên
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRate(2)}
                      className="rounded-2xl border border-amber-200 bg-amber-50/70 py-3 text-xs font-bold text-amber-700 hover:bg-amber-100 transition-colors"
                      title="Phím tắt: 2"
                    >
                      🟠 [2] Khó
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRate(3)}
                      className="rounded-2xl border border-blue-200 bg-blue-50/70 py-3 text-xs font-bold text-blue-700 hover:bg-blue-100 transition-colors"
                      title="Phím tắt: 3"
                    >
                      🔵 [3] Tốt
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRate(4)}
                      className="rounded-2xl border border-emerald-200 bg-emerald-50/70 py-3 text-xs font-bold text-emerald-700 hover:bg-emerald-100 transition-colors"
                      title="Phím tắt: 4"
                    >
                      🟢 [4] Dễ
                    </button>
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
