import { Languages, BookOpen, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "../hooks/useTranslation";
import { LANG_CONFIG } from "../services/deckStorage";
import { TranslationBox } from "../components/translation/TranslationBox";
import { isDocTranslationEnabled } from "../config";

export default function TranslationPage() {
  const navigate = useNavigate();
  const {
    sourceLang,
    targetLang,
    sourceText,
    setSourceLang,
    setTargetLang,
    setSourceText,
    swapLanguages,
  } = useTranslation();

  const targetLangMeta = LANG_CONFIG[targetLang] || {
    label: targetLang.toUpperCase(),
    flag: "🌐",
    defaultTitle: `Sổ từ vựng ${targetLang.toUpperCase()}`,
  };

  return (
    <div className="min-h-full w-full">
      <div className="mx-auto flex h-full max-w-6xl flex-col p-4 sm:p-6 lg:p-8">
        {/* Top Header */}
        <div className="mb-6 flex flex-col justify-between gap-4 sm:mb-8 sm:gap-6 sm:flex-row sm:items-center">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 shadow-lg shadow-brand-600/30">
                <Languages className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100">Translation Studio</h1>
            </div>
            <p className="mt-2 text-sm text-slate-500 font-medium dark:text-slate-400">Dịch thuật đa ngôn ngữ chuyên ngành với AI & Lưu Flashcard thông minh</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {isDocTranslationEnabled() && (
              <button
                type="button"
                onClick={() => navigate("/translation-doc")}
                className="group flex min-h-[44px] flex-1 items-center justify-center gap-2 sm:flex-none rounded-xl border border-brand-200 bg-brand-50/80 px-4 py-2.5 dark:bg-brand-950/40 text-sm font-semibold text-brand-700 backdrop-blur-sm transition-all hover:bg-brand-100 hover:shadow-sm hover:shadow-brand-200/50 dark:border-brand-800 dark:text-brand-300 dark:hover:bg-brand-900/50"
              >
                <FileText size={18} className="transition-transform group-hover:scale-110" />
                <span>Dịch Tài Liệu</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => navigate("/flashcards")}
              className="group flex min-h-[44px] flex-1 items-center justify-center gap-2 sm:flex-none rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 text-sm font-semibold text-slate-700 backdrop-blur-sm transition-all hover:bg-slate-50 hover:shadow-sm dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700 dark:bg-slate-800/80"
            >
              <BookOpen size={18} className="transition-transform group-hover:scale-110" />
              <span>Sổ Thẻ Flashcard</span>
            </button>
          </div>
        </div>

        {/* Translation Box Area */}
        <div className="flex-1">
          <TranslationBox 
            sourceLang={sourceLang}
            targetLang={targetLang}
            sourceText={sourceText}
            setSourceLang={setSourceLang}
            setTargetLang={setTargetLang}
            setSourceText={setSourceText}
            swapLanguages={swapLanguages}
            targetLangMeta={targetLangMeta}
          />
        </div>
      </div>
    </div>
  );
}
