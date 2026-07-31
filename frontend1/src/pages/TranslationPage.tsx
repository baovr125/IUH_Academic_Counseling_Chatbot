import { useState } from "react";
import { ArrowRightLeft, BookmarkPlus, CheckCircle2, Languages, Sparkles, BookOpen, FileText, AlignLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "../hooks/useTranslation";
import { LANG_CONFIG, addCardToDeck } from "../services/deckStorage";

const SAMPLE_QUICK_PHRASES = [
  "tôi muốn đăng ký tín chỉ",
  "chào bạn",
  "cảm ơn bạn",
  "khoa công nghệ thông tin",
];

export default function TranslationPage() {
  const navigate = useNavigate();
  const {
    sourceLang,
    targetLang,
    sourceText,
    translatedText,
    isTranslating,
    setSourceLang,
    setTargetLang,
    setSourceText,
    swapLanguages,
    translate,
  } = useTranslation();

  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const handleSaveToDeck = () => {
    if (!sourceText.trim() || !translatedText.trim()) return;

    const result = addCardToDeck(
      targetLang,
      sourceText,
      translatedText,
      `Dịch từ ${LANG_CONFIG[sourceLang]?.label || sourceLang} -> ${LANG_CONFIG[targetLang]?.label || targetLang}`,
      "phrase"
    );

    setSavedMessage(`Đã lưu "${sourceText.slice(0, 25)}..." vào sổ thẻ '${result.deck.title}' (${result.deck.iconFlag})`);
    setTimeout(() => {
      setSavedMessage(null);
    }, 5000);
  };

  const targetLangMeta = LANG_CONFIG[targetLang] || {
    label: targetLang.toUpperCase(),
    flag: "🌐",
    defaultTitle: `Sổ từ vựng ${targetLang.toUpperCase()}`,
  };

  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col p-6">
      {/* Top Header */}
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Languages className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-800">Dịch thuật Đa Ngôn Ngữ (Translation Studio)</h1>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Dịch thuật hỗ trợ 10 ngôn ngữ và tự động lưu từ vựng vào các sổ thẻ riêng biệt theo ngôn ngữ đích
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate("/translation-doc")}
            className="flex items-center gap-1.5 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors"
          >
            <FileText size={16} />
            <span>Dịch Tài Liệu (PDF/PPT/Word)</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/flashcards")}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <BookOpen size={16} />
            <span>Sổ Thẻ Flashcard</span>
          </button>
        </div>
      </div>

      {/* Mode Switcher Banner */}
      <div className="mb-6 flex gap-2 border-b border-slate-200 pb-px">
        <button
          type="button"
          className="flex items-center gap-2 border-b-2 border-blue-600 px-4 py-2.5 text-xs font-semibold text-blue-600 transition-colors"
        >
          <AlignLeft size={15} />
          <span>Dịch Văn Bản Ngắn (Text Translation)</span>
        </button>
        <button
          type="button"
          onClick={() => navigate("/translation-doc")}
          className="flex items-center gap-2 border-b-2 border-transparent px-4 py-2.5 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors"
        >
          <FileText size={15} />
          <span>Dịch Tài Liệu (PDF, PowerPoint, Word)</span>
        </button>
      </div>

      {/* Success Notification Banner */}
      {savedMessage && (
        <div className="mb-4 flex items-center justify-between rounded-xl border border-green-200 bg-green-50 p-3.5 text-xs font-medium text-green-800 shadow-sm animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 size={18} className="text-green-600 flex-shrink-0" />
            <span>{savedMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => navigate("/flashcards")}
            className="rounded-lg bg-green-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-green-700 transition-colors"
          >
            Mở Flashcard ngay
          </button>
        </div>
      )}

      {/* Language Selector Bar */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          {/* Source Language Select */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Từ:</span>
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 focus:border-blue-500 focus:outline-none"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={swapLanguages}
            title="Đổi chiều ngôn ngữ"
            className="rounded-full border border-slate-200 p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-600 transition-colors"
          >
            <ArrowRightLeft size={16} />
          </button>

          {/* Target Language Select */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Sang:</span>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 focus:border-blue-500 focus:outline-none"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={translate}
          disabled={isTranslating || !sourceText.trim()}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Sparkles size={15} />
          <span>{isTranslating ? "Đang dịch..." : "Dịch ngay"}</span>
        </button>
      </div>

      {/* Quick Phrases for Demo */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-slate-400">Mẫu câu nhanh:</span>
        {SAMPLE_QUICK_PHRASES.map((phrase) => (
          <button
            type="button"
            key={phrase}
            onClick={() => setSourceText(phrase)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 hover:border-blue-300 hover:bg-blue-50/50 hover:text-blue-600 transition-colors"
          >
            "{phrase}"
          </button>
        ))}
      </div>

      {/* Translation Panels */}
      <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-2 min-h-[300px]">
        {/* Source Textarea */}
        <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">
              Văn bản gốc ({LANG_CONFIG[sourceLang]?.flag} {LANG_CONFIG[sourceLang]?.label || sourceLang})
            </span>
            {sourceText && (
              <button
                type="button"
                onClick={() => setSourceText("")}
                className="text-[11px] text-slate-400 hover:text-red-500"
              >
                Xóa
              </button>
            )}
          </div>
          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder='Nhập nội dung cần dịch hoặc bấm chọn "Mẫu câu nhanh" ở trên...'
            className="w-full flex-1 resize-none border-none p-2 text-sm text-slate-800 focus:outline-none"
          />
        </div>

        {/* Translated Textarea + Save to Deck Button */}
        <div className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-slate-50/70 p-4 shadow-sm">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-600">
                Bản dịch ({targetLangMeta.flag} {targetLangMeta.label})
              </span>
              <span className="text-[11px] font-medium text-slate-400">
                AI Neural Translate
              </span>
            </div>
            <div className="p-2 text-sm text-slate-800 min-h-[160px]">
              {isTranslating ? (
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="h-2 w-2 animate-ping rounded-full bg-blue-500" />
                  <span>Đang phân tích & dịch văn bản...</span>
                </div>
              ) : translatedText ? (
                <p className="whitespace-pre-wrap leading-relaxed font-medium text-slate-800">
                  {translatedText}
                </p>
              ) : (
                <span className="text-slate-400 italic">
                  Kết quả dịch sẽ xuất hiện ở đây...
                </span>
              )}
            </div>
          </div>

          {/* Button Lưu từ vào Sổ thẻ (Flashcard Deck) */}
          <div className="mt-4 border-t border-slate-200/80 pt-4 flex items-center justify-between">
            <div className="text-[11px] text-slate-500">
              Sổ thẻ tương ứng:{" "}
              <span className="font-semibold text-slate-700">
                {targetLangMeta.flag} {targetLangMeta.defaultTitle}
              </span>
            </div>

            <button
              type="button"
              onClick={handleSaveToDeck}
              disabled={!translatedText || isTranslating}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <BookmarkPlus size={16} />
              <span>Lưu từ vào Sổ thẻ ({targetLangMeta.flag})</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
