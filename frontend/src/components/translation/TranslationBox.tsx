import React, { useState, useEffect, useRef } from "react";
import { streamTranslation, extractFlashcard } from "../../services/translationService";
import { FloatingMenu } from "./FloatingMenu";
import { DomainSelector } from "./DomainSelector";
import { BookmarkPlus, ArrowRightLeft, Volume2, X, Loader2 } from "lucide-react";
import { LANG_CONFIG } from "../../services/deckStorage";
import { SaveFlashcardModal } from "./SaveFlashcardModal";

export interface TranslationBoxProps {
  sourceLang: string;
  targetLang: string;
  sourceText: string;
  setSourceLang: (lang: string) => void;
  setTargetLang: (lang: string) => void;
  setSourceText: (text: string) => void;
  swapLanguages: () => void;
  onSaveFullTranslation?: (translatedText: string) => void;
  targetLangMeta: { flag: string; label: string; defaultTitle: string };
}

export const TranslationBox: React.FC<TranslationBoxProps> = ({
  sourceLang,
  targetLang,
  sourceText,
  setSourceLang,
  setTargetLang,
  setSourceText,
  swapLanguages,
  onSaveFullTranslation,
  targetLangMeta
}) => {
  const [domain, setDomain] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Array of parsed tokens/words for the UI
  const [translatedTokens, setTranslatedTokens] = useState<string[]>([]);
  
  // Selection state for Floating Menu
  const [menuPosition, setMenuPosition] = useState<{ x: number, y: number } | null>(null);
  const [selectedWord, setSelectedWord] = useState("");
  const [selectedContext, setSelectedContext] = useState("");
  const [isSavingFlashcard, setIsSavingFlashcard] = useState(false);
  
  // Save Flashcard Modal State
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [modalTerm, setModalTerm] = useState("");
  const [modalDef, setModalDef] = useState("");
  const [modalLang, setModalLang] = useState("en");
  const [modalContext, setModalContext] = useState("");
  const [modalPhonetic, setModalPhonetic] = useState("");

  // Toast state
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  const [speakingId, setSpeakingId] = useState<"source" | "target" | "selection" | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCache = useRef<Map<string, string>>(new Map());
  
  // Debounce ref to handle real-time streaming
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ttsDebounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const getTTSLangCode = (langCode: string) => {
    const map: Record<string, string> = {
      en: "en-US",
      de: "de-DE",
      zh: "zh-CN",
      ja: "ja-JP",
      ko: "ko-KR",
      fr: "fr-FR",
      es: "es-ES",
      ru: "ru-RU",
      th: "th-TH",
      vi: "vi-VN"
    };
    const clean = (langCode || "en").toLowerCase().replace("_", "-");
    return map[clean] || map[clean.slice(0, 2)] || "en-US";
  };

  const getApiBaseUrl = (): string => {
    const env = (import.meta as any).env || {};
    const base = env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "http://localhost:8000";
    return String(base).replace(/\/+$/, "");
  };

  // Prefetch audio and cache as Blob URL
  const prefetchAudio = async (text: string, lang: string) => {
    if (!text.trim() || text.trim().length < 2) return;
    const cacheKey = `${lang}_${text}`;
    if (audioCache.current.has(cacheKey)) return;

    try {
      const baseUrl = getApiBaseUrl();
      const url = `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(text)}&lang=${lang}`;
      const response = await fetch(url);
      if (response.ok) {
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        audioCache.current.set(cacheKey, objectUrl);
      }
    } catch (e) {
      console.error("Prefetch audio failed:", e);
    }
  };

  const playbackSessionRef = useRef<number>(0);

  // Deep teardown of any active HTML5 audio and browser speech synthesis
  const cleanupCurrentAudio = () => {
    if (audioRef.current) {
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.oncanplay = null;
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current.removeAttribute("src");
      audioRef.current.load();
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  };

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      playbackSessionRef.current++;
      cleanupCurrentAudio();
    };
  }, []);

  // Neural Edge TTS from Backend with Toggle-to-stop & Spam Protection
  const speakText = async (text: string, lang: string = "vi-VN", id: "source" | "target" | "selection") => {
    if (!text || !text.trim()) return;

    // Toggle behavior: if currently speaking this specific section, stop it
    if (speakingId === id) {
      playbackSessionRef.current++;
      cleanupCurrentAudio();
      setSpeakingId(null);
      return;
    }

    // Stop currently playing audio cleanly
    cleanupCurrentAudio();
    const sessionId = ++playbackSessionRef.current;
    setSpeakingId(id);

    const cacheKey = `${lang}_${text.trim()}`;
    let audioUrl = audioCache.current.get(cacheKey);
    const baseUrl = getApiBaseUrl();

    if (!audioUrl) {
      audioUrl = `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(text.trim())}&lang=${encodeURIComponent(lang)}`;
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.onended = () => {
      if (playbackSessionRef.current === sessionId) {
        setSpeakingId(null);
      }
    };

    audio.onerror = () => {
      if (playbackSessionRef.current === sessionId) {
        setSpeakingId(null);
      }
    };

    audio.play().catch((e: any) => {
      if (e?.name === "AbortError" || playbackSessionRef.current !== sessionId) {
        // Interrupted by new click or pause, silently ignore
        return;
      }
      console.error("TTS Play Error:", e);
      if (playbackSessionRef.current === sessionId) {
        setSpeakingId(null);
      }
    });
  };

  const handleTranslate = (textToTranslate: string = sourceText) => {
    if (!textToTranslate.trim()) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setTranslatedTokens([]);
      setIsTranslating(false);
      return;
    }
    
    // Cancel any pending translation stream before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const newAbortController = new AbortController();
    abortControllerRef.current = newAbortController;

    setIsTranslating(true);
    setError(null);
    setTranslatedTokens([]);
    setMenuPosition(null);

    let currentBuffer = "";
    
    streamTranslation(
      {
        sourceText: textToTranslate,
        sourceLang: sourceLang as any,
        targetLang: targetLang as any,
        domain: domain
      },
      (token: string) => {
        currentBuffer += token;
        setTranslatedTokens((prev) => [...prev, token]);
      },
      (err: string) => {
        setIsTranslating(false);
        setError(err || "Đã xảy ra lỗi trong quá trình dịch thuật.");
      },
      () => {
        setIsTranslating(false);
      },
      newAbortController.signal
    );
  };

  // Debounced input change translation (200ms fast real-time typing)
  useEffect(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    
    if (sourceText.trim()) {
      debounceTimerRef.current = setTimeout(() => {
        handleTranslate(sourceText);
      }, 200); // 200ms fast debounce
    } else {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setTranslatedTokens([]);
      setIsTranslating(false);
    }
    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [sourceText, sourceLang, targetLang, domain]);

  // TTS Prefetch Effect: Trigger with 900ms (0.9s) debounce when translation finishes
  useEffect(() => {
    if (ttsDebounceTimerRef.current) {
      clearTimeout(ttsDebounceTimerRef.current);
    }

    if (!isTranslating) {
      const translated = translatedTokens.join("");
      const hasValidTarget = translated.trim().length >= 2;
      const hasValidSource = sourceText.trim().length >= 2;

      if (hasValidTarget || hasValidSource) {
        ttsDebounceTimerRef.current = setTimeout(() => {
          if (hasValidTarget) {
            prefetchAudio(translated.trim(), getTTSLangCode(targetLang));
          }
          if (hasValidSource) {
            prefetchAudio(sourceText.trim(), getTTSLangCode(sourceLang));
          }
        }, 900); // 900ms (0.9s) debounce for TTS
      }
    }

    return () => {
      if (ttsDebounceTimerRef.current) {
        clearTimeout(ttsDebounceTimerRef.current);
      }
    };
  }, [isTranslating, translatedTokens, sourceText, sourceLang, targetLang]);

  const handleSwap = () => {
    const currentTranslated = translatedTokens.join("");
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    // Google Translate behavior: when swapping, the translated text becomes the new source text
    if (currentTranslated.trim()) {
      setSourceText(currentTranslated);
    }
  };

  const handleSelection = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !containerRef.current) {
      if (!isSavingFlashcard) setMenuPosition(null);
      return;
    }

    // Ensure selection is inside our container
    if (!containerRef.current.contains(selection.anchorNode)) {
      return;
    }

    const text = selection.toString().trim();
    if (!text) return;

    // Get position for the floating menu
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    // Get full sentence context (rough approximation)
    const allText = translatedTokens.join("");
    // Find the sentence containing the text
    const sentenceRegex = new RegExp(`[^.?!]*(?<=[.?\\s!])${text.replace(/[.*+?^$\\{}()[\]\\]/g, '\\$&')}(?=[\\s.?!])[^.?!]*[.?!]?`, 'i');
    const match = allText.match(sentenceRegex);
    const context = match ? match[0].trim() : allText.slice(0, 150);

    setSelectedWord(text);
    setSelectedContext(context);
    setMenuPosition({
      x: rect.left + rect.width / 2,
      y: rect.top + window.scrollY
    });
  };

  const saveFlashcard = async () => {
    if (!selectedWord) return;
    
    setIsSavingFlashcard(true);
    setToastMessage(`Đang phân tích từ vựng "${selectedWord}"...`);
    
    try {
      const res = await extractFlashcard(selectedWord, selectedContext, domain);
      setIsSavingFlashcard(false);
      setMenuPosition(null);
      setToastMessage(null);
      
      const extractedDef = res.ok && res.data?.definition ? res.data.definition : "";
      const extractedPhonetic = res.ok && res.data?.phonetic ? res.data.phonetic : "";
      
      setModalTerm(selectedWord.trim());
      setModalDef(extractedDef || selectedWord.trim());
      setModalLang(targetLang === "vi" ? sourceLang : targetLang);
      setModalContext(selectedContext);
      setModalPhonetic(extractedPhonetic);
      setIsSaveModalOpen(true);
    } catch {
      setIsSavingFlashcard(false);
      setMenuPosition(null);
      setToastMessage(null);
      setModalTerm(selectedWord.trim());
      setModalDef("");
      setModalLang(targetLang === "vi" ? sourceLang : targetLang);
      setModalContext(selectedContext);
      setModalPhonetic("");
      setIsSaveModalOpen(true);
    }
  };

  const handleOpenFullSaveModal = () => {
    const translated = translatedTokens.join("");
    if (!sourceText.trim() || !translated.trim()) return;

    if (targetLang === "vi") {
      setModalTerm(sourceText.trim());
      setModalDef(translated.trim());
      setModalLang(sourceLang);
    } else {
      setModalTerm(translated.trim());
      setModalDef(sourceText.trim());
      setModalLang(targetLang);
    }
    setModalContext(sourceText.trim());
    setModalPhonetic("");
    setIsSaveModalOpen(true);
  };

  const speakSelection = () => {
    speakText(selectedWord, getTTSLangCode(targetLang === "vi" ? sourceLang : targetLang), "selection");
    setMenuPosition(null);
  };

  return (
    <div className="w-full relative">
      {/* Translation Main Card */}
      <div className="relative flex flex-col md:flex-row bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden min-h-[450px]">
        
        {/* Source Text Area */}
        <div className="flex-1 flex flex-col border-b md:border-b-0 md:border-r border-slate-200 focus-within:bg-slate-50/50 transition-colors">
          {/* Header */}
          <div className="flex items-center px-6 py-4 border-b border-slate-100 bg-white">
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              className="bg-transparent text-sm font-semibold text-slate-700 focus:outline-none cursor-pointer"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>
          
          <textarea
            className="flex-1 w-full px-6 py-5 bg-transparent resize-none outline-none text-slate-800 text-lg leading-relaxed placeholder:text-slate-400"
            placeholder="Nhập văn bản cần dịch tại đây..."
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value.slice(0, 3000))}
          />
          <div className="px-6 py-3 flex items-center justify-between text-xs font-medium text-slate-400 bg-white">
             <div className="flex items-center gap-1">
               {sourceText && (
                 <button onClick={() => setSourceText("")} className="hover:text-red-500 transition-colors p-2 rounded-lg hover:bg-red-50" title="Xóa văn bản">
                   <X size={18} />
                 </button>
               )}
               {sourceText && (
                  <button onClick={() => speakText(sourceText, getTTSLangCode(sourceLang), "source")} className="hover:text-blue-500 transition-colors p-2 rounded-lg hover:bg-blue-50" title="Đọc văn bản">
                    {speakingId === "source" ? <Loader2 size={18} className="animate-spin" /> : <Volume2 size={18} />}
                  </button>
               )}
             </div>
             <span className={sourceText.length >= 3000 ? "text-red-500 font-semibold" : ""}>
               {sourceText.length} / 3000
             </span>
          </div>
        </div>

        {/* Desktop Swap Button */}
        <div className="hidden md:flex absolute left-1/2 top-[30px] -translate-x-1/2 -translate-y-1/2 z-10">
           <button
             onClick={handleSwap}
             className="flex items-center justify-center w-10 h-10 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:text-blue-600 hover:border-blue-200 transition-transform hover:scale-105 active:scale-95"
             title="Đổi ngôn ngữ"
           >
             <ArrowRightLeft size={16} />
           </button>
        </div>

        {/* Translation Output Area */}
        <div 
          className="flex-1 flex flex-col bg-slate-50"
          ref={containerRef}
          onMouseUp={handleSelection}
        >
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 border-b border-slate-100 bg-white">
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="bg-transparent text-sm font-semibold text-blue-700 focus:outline-none cursor-pointer"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
            
            <DomainSelector value={domain} onChange={setDomain} />
          </div>
          
          <div className="flex-1 px-6 py-5 overflow-y-auto leading-relaxed text-slate-800 text-lg selection:bg-blue-200 selection:text-blue-900">
            {translatedTokens.length === 0 && !isTranslating && !error && (
              <span className="text-slate-400 font-light italic">
                Bản dịch sẽ xuất hiện tại đây...
              </span>
            )}
            
            {error && (
              <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm border border-red-100">
                {error}
              </div>
            )}
            
            <div className="whitespace-pre-wrap relative">
              {translatedTokens.map((token, i) => (
                <span key={i} className="hover:bg-blue-100/50 rounded-sm transition-colors cursor-text">
                  {token}
                </span>
              ))}
              {isTranslating && (
                <span className="inline-block w-2 h-5 ml-1 bg-blue-500/80 rounded-sm animate-pulse align-middle"></span>
              )}
            </div>
          </div>
          
          <div className="px-6 py-4 flex items-center justify-between border-t border-slate-200/50 bg-slate-50">
             <div className="flex items-center gap-2">
               {translatedTokens.length > 0 && (
                  <button onClick={() => speakText(translatedTokens.join(''), getTTSLangCode(targetLang), "target")} className="text-slate-500 hover:text-blue-600 transition-colors p-2 rounded-lg hover:bg-white border border-transparent hover:border-slate-200 shadow-sm" title="Đọc bản dịch">
                    {speakingId === "target" ? <Loader2 size={18} className="animate-spin" /> : <Volume2 size={18} />}
                  </button>
               )}
             </div>
             <button
              type="button"
              onClick={handleOpenFullSaveModal}
              disabled={translatedTokens.length === 0 || isTranslating}
              className="group flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-[1.02] active:scale-[0.98]"
             >
              <BookmarkPlus size={18} className="transition-transform group-hover:scale-110" />
              <span>Lưu Flashcard</span>
             </button>
          </div>
        </div>
      </div>

      {/* Floating Menu Portal */}
      {menuPosition && (
        <FloatingMenu
          x={menuPosition.x}
          y={menuPosition.y}
          onSave={saveFlashcard}
          onSpeak={speakSelection}
          onClose={() => setMenuPosition(null)}
          isSaving={isSavingFlashcard}
        />
      )}

      {/* Save to Flashcard Modal */}
      <SaveFlashcardModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        initialTerm={modalTerm}
        initialDefinition={modalDef}
        initialLangCode={modalLang}
        initialContext={modalContext}
        initialPhonetic={modalPhonetic}
        onSuccess={(deckTitle, term) => {
          setToastMessage(`Đã lưu "${term}" vào sổ thẻ "${deckTitle}" thành công! 🎉`);
          setTimeout(() => setToastMessage(null), 4000);
        }}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-4">
          <div className="bg-slate-800 text-white px-5 py-3.5 rounded-xl shadow-xl shadow-slate-900/20 text-sm font-medium flex items-center gap-3 border border-slate-700/50 backdrop-blur-md">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            {toastMessage}
          </div>
        </div>
      )}
      
    </div>
  );
};
