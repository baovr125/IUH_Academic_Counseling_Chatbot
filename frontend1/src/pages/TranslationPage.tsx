import { ArrowRightLeft } from "lucide-react";
import { useTranslation } from "../hooks/useTranslation";

const LANG_LABEL: Record<string, string> = { vi: "Vietnamese", en: "English", de: "German" };

export default function TranslationPage() {
  const {
    sourceLang,
    targetLang,
    sourceText,
    translatedText,
    isTranslating,
    setSourceText,
    swapLanguages,
    translate,
  } = useTranslation();

  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-4 flex items-center gap-3">
        <span className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm">{LANG_LABEL[sourceLang]}</span>
        <button onClick={swapLanguages} className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100">
          <ArrowRightLeft size={16} />
        </button>
        <span className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm">{LANG_LABEL[targetLang]}</span>

        <button
          onClick={translate}
          disabled={isTranslating || !sourceText.trim()}
          className="ml-auto rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isTranslating ? "Translating..." : "Translate Now"}
        </button>
      </div>

      <div className="grid flex-1 grid-cols-2 gap-4">
        <textarea
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
          placeholder='Ví dụ: "tôi muốn đăng ký tín chỉ"'
          className="resize-none rounded-xl border border-slate-200 bg-white p-4 text-sm focus:border-blue-400 focus:outline-none"
        />
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          {isTranslating ? (
            <span className="text-slate-400">Đang dịch...</span>
          ) : (
            translatedText || <span className="text-slate-400">Translation output...</span>
          )}
        </div>
      </div>
    </div>
  );
}
