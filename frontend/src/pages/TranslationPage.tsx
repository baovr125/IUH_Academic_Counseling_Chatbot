import { Languages, BookOpen, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "../hooks/useTranslation";
import { LANG_CONFIG } from "../services/deckStorage";
import { TranslationBox } from "../components/translation/TranslationBox";

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
    <div className="min-h-full w-full bg-gradient-to-br from-indigo-50/50 via-white to-blue-50/50">
      <div className="mx-auto flex h-full max-w-6xl flex-col p-6 lg:p-8">
        {/* Top Header */}
        <div className="mb-8 flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-600/30">
                <Languages className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-800">Translation Studio</h1>
            </div>
            <p className="mt-2 text-sm text-slate-500 font-medium">Dịch thuật đa ngôn ngữ chuyên ngành với AI & Lưu Flashcard thông minh</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate("/translation-doc")}
              className="group flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50/80 px-4 py-2.5 text-sm font-semibold text-blue-700 backdrop-blur-sm transition-all hover:bg-blue-100 hover:shadow-sm hover:shadow-blue-200/50"
            >
              <FileText size={18} className="transition-transform group-hover:scale-110" />
              <span>Dịch Tài Liệu</span>
            </button>

            <button
              type="button"
              onClick={() => navigate("/flashcards")}
              className="group flex items-center gap-2 rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 text-sm font-semibold text-slate-700 backdrop-blur-sm transition-all hover:bg-slate-50 hover:shadow-sm"
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
