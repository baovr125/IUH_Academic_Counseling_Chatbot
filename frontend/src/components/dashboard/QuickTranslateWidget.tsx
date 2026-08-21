import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Languages,
  ArrowRightLeft,
  Sparkles,
  BookPlus,
  Check,
  Copy,
  ExternalLink,
  Loader2,
  Volume2,
} from "lucide-react";
import { translateText } from "../../services/translationService";
import { addCardToDeck, getDecks, createCustomDeck, LANG_CONFIG } from "../../services/deckStorage";
import { useAuth } from "../../hooks/useAuth";

const POPULAR_LANGUAGES = [
  { code: "en", label: "Tiếng Anh", flag: "🇬🇧" },
  { code: "vi", label: "Tiếng Việt", flag: "🇻🇳" },
  { code: "ja", label: "Tiếng Nhật", flag: "🇯🇵" },
  { code: "ko", label: "Tiếng Hàn", flag: "🇰🇷" },
  { code: "zh", label: "Tiếng Trung", flag: "🇨🇳" },
  { code: "de", label: "Tiếng Đức", flag: "🇩🇪" },
  { code: "fr", label: "Tiếng Pháp", flag: "🇫🇷" },
];

export const QuickTranslateWidget: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [sourceLang, setSourceLang] = useState("vi");
  const [targetLang, setTargetLang] = useState("en");
  const [inputText, setInputText] = useState("");
  const [translatedResult, setTranslatedResult] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [isSavedFlashcard, setIsSavedFlashcard] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleSwap = () => {
    const tempLang = sourceLang;
    setSourceLang(targetLang);
    setTargetLang(tempLang);
    setInputText(translatedResult);
    setTranslatedResult(inputText);
    setIsSavedFlashcard(false);
  };

  const handleTranslate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim()) return;

    setIsTranslating(true);
    setIsSavedFlashcard(false);
    try {
      const res = await translateText({
        sourceText: inputText.trim(),
        sourceLang,
        targetLang,
      });

      if (res.ok && res.data) {
        setTranslatedResult(res.data.translatedText);
      }
    } catch (err) {
      console.error("Translation error in widget:", err);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleSaveToFlashcard = () => {
    if (!inputText.trim() || !translatedResult.trim()) return;

    try {
      const term = targetLang === "vi" ? inputText.trim() : translatedResult.trim();
      const definition = targetLang === "vi" ? translatedResult.trim() : inputText.trim();
      const example = `IUH Academic Context: ${inputText.trim()}`;

      addCardToDeck(
        targetLang,
        term,
        definition,
        example,
        "noun",
        undefined,
        user?.id
      );

      setIsSavedFlashcard(true);
      setTimeout(() => setIsSavedFlashcard(false), 3000);
    } catch (e) {
      console.error("Error saving card:", e);
    }
  };


  const handleCopy = () => {
    if (!translatedResult) return;
    navigator.clipboard.writeText(translatedResult);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4 dark:border-slate-700/60">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
            <Languages size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
              Dịch thuật Đa Ngôn ngữ Nhanh (Redis Cache &lt;5ms)
            </h3>
            <p className="text-[11px] text-slate-400">Tra cứu nhanh từ vựng chuyên ngành & lưu thẻ học</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => navigate("/translation")}
          className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          <span>Mở Studio Dịch</span>
          <ExternalLink size={13} />
        </button>
      </div>

      {/* Language Selectors & Swap */}
      <div className="mt-4 flex items-center justify-between gap-3">
        <div className="flex-1">
          <select
            value={sourceLang}
            onChange={(e) => setSourceLang(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 focus:outline-none focus:border-blue-500"
          >
            {POPULAR_LANGUAGES.map((lang) => (
              <option key={`src_${lang.code}`} value={lang.code}>
                {lang.flag} {lang.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={handleSwap}
          className="flex h-8 w-8 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-transform active:scale-95 shadow-sm cursor-pointer"
          title="Đảo chiều ngôn ngữ"
        >
          <ArrowRightLeft size={14} />
        </button>

        <div className="flex-1">
          <select
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 focus:outline-none focus:border-blue-500"
          >
            {POPULAR_LANGUAGES.map((lang) => (
              <option key={`tgt_${lang.code}`} value={lang.code}>
                {lang.flag} {lang.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Input & Output Translation Grid */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Source Box */}
        <div className="flex flex-col rounded-2xl border border-slate-200 bg-slate-50/50 p-3.5 dark:border-slate-700 dark:bg-slate-900/50">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleTranslate();
              }
            }}
            placeholder="Nhập từ hoặc câu cần dịch (ví dụ: tôi muốn đăng ký tín chỉ)..."
            rows={3}
            className="w-full resize-none bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder-slate-500"
          />
          <div className="mt-2 flex items-center justify-between pt-2 border-t border-slate-200/60 dark:border-slate-800">
            <span className="text-[11px] text-slate-400">{inputText.length} ký tự</span>
            <button
              type="button"
              onClick={() => handleTranslate()}
              disabled={isTranslating || !inputText.trim()}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer"
            >
              {isTranslating ? (
                <>
                  <Loader2 size={13} className="animate-spin" />
                  <span>Đang dịch...</span>
                </>
              ) : (
                <>
                  <Sparkles size={13} />
                  <span>Dịch Ngay</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Target Box */}
        <div className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-blue-50/30 p-3.5 dark:border-slate-700 dark:bg-slate-900/80">
          <div className="min-h-[60px]">
            {translatedResult ? (
              <p className="text-xs font-medium text-slate-800 dark:text-slate-100 leading-relaxed select-text">
                {translatedResult}
              </p>
            ) : (
              <p className="text-xs italic text-slate-400">Kết quả dịch thuật AI sẽ hiển thị tại đây...</p>
            )}
          </div>

          {translatedResult && (
            <div className="mt-2 flex items-center justify-between pt-2 border-t border-slate-200/60 dark:border-slate-800">
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] text-slate-500 hover:bg-slate-200/60 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
                title="Sao chép"
              >
                {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
                <span>{copied ? "Đã chép" : "Sao chép"}</span>
              </button>

              <button
                type="button"
                onClick={handleSaveToFlashcard}
                className={`flex items-center gap-1.5 rounded-xl px-2.5 py-1 text-xs font-semibold shadow-sm transition-all cursor-pointer ${
                  isSavedFlashcard
                    ? "bg-emerald-600 text-white"
                    : "bg-orange-500 text-white hover:bg-orange-600"
                }`}
              >
                {isSavedFlashcard ? (
                  <>
                    <Check size={13} />
                    <span>Đã lưu vào Flashcard</span>
                  </>
                ) : (
                  <>
                    <BookPlus size={13} />
                    <span>+ Lưu Flashcard</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
