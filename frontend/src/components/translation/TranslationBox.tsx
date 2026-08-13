import React, { useState, useEffect, useRef } from "react";
import { streamTranslation, extractFlashcard } from "../../services/translationService";
import { FloatingMenu } from "./FloatingMenu";
import { DomainSelector } from "./DomainSelector";
import { BookmarkPlus, ArrowRightLeft, Volume2, X } from "lucide-react";
import { LANG_CONFIG } from "../../services/deckStorage";

export interface TranslationBoxProps {
  sourceLang: string;
  targetLang: string;
  sourceText: string;
  setSourceLang: (lang: string) => void;
  setTargetLang: (lang: string) => void;
  setSourceText: (text: string) => void;
  swapLanguages: () => void;
  onSaveFullTranslation: (translatedText: string) => void;
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
  
  // Toast state
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Debounce ref to handle real-time streaming
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
    return map[langCode] || "en-US";
  };

  // Neural Edge TTS from Backend
  const speakText = (text: string, lang: string = "vi-VN") => {
    if (!text) return;
    
    // Stop currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const url = `/api/v1/translate/tts?text=${encodeURIComponent(text)}&lang=${lang}`;
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.play().catch(e => console.error("TTS Play Error:", e));
  };

  const handleTranslate = (textToTranslate: string = sourceText) => {
    if (!textToTranslate.trim()) {
      setTranslatedTokens([]);
      return;
    }
    
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
      (chunk) => {
        // Simple Tokenizer: buffer chunks and split by space to keep words together
        currentBuffer += chunk;
        const words = currentBuffer.split(/(\s+)/);
        
        // Keep the last incomplete part in the buffer, push the rest
        if (words.length > 1) {
          const completeWords = words.slice(0, -1);
          setTranslatedTokens(prev => [...prev, ...completeWords]);
          currentBuffer = words[words.length - 1];
        }
      },
      (err) => {
        setError(err);
        setIsTranslating(false);
      },
      () => {
        if (currentBuffer) {
          setTranslatedTokens(prev => [...prev, currentBuffer]);
        }
        setIsTranslating(false);
      }
    );
  };

  // Real-time Translation Effect (Debounce)
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (sourceText.trim()) {
      debounceTimerRef.current = setTimeout(() => {
        handleTranslate(sourceText);
      }, 800);
    } else {
      setTranslatedTokens([]);
      setIsTranslating(false);
      setError(null);
    }
    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [sourceText, sourceLang, targetLang, domain]);

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
    
    const res = await extractFlashcard(selectedWord, selectedContext, domain);
    
    setIsSavingFlashcard(false);
    setMenuPosition(null);
    
    if (res.ok) {
      setToastMessage(`Đã lưu "${selectedWord}" vào bộ thẻ!`);
      // Hide toast after 3s
      setTimeout(() => setToastMessage(null), 3000);
    } else {
      setToastMessage(`Lỗi khi lưu thẻ: ${res.error?.message}`);
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  const speakSelection = () => {
    speakText(selectedWord, getTTSLangCode(targetLang));
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
              className="bg-transparent text-sm font-semibold text-slate-700 hover:text-blue-600 focus:outline-none cursor-pointer"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
            <div className="md:hidden ml-auto">
               <button
                 onClick={swapLanguages}
                 className="p-2 text-slate-500 hover:text-blue-600 bg-slate-50 rounded-full border border-slate-200"
               >
                 <ArrowRightLeft size={16} />
               </button>
            </div>
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
                  <button onClick={() => speakText(sourceText, getTTSLangCode(sourceLang))} className="hover:text-blue-500 transition-colors p-2 rounded-lg hover:bg-blue-50" title="Đọc văn bản">
                    <Volume2 size={18} />
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
                  <button onClick={() => speakText(translatedTokens.join(''), getTTSLangCode(targetLang))} className="text-slate-500 hover:text-blue-600 transition-colors p-2 rounded-lg hover:bg-white border border-transparent hover:border-slate-200 shadow-sm" title="Đọc bản dịch">
                    <Volume2 size={18} />
                  </button>
               )}
             </div>
             <button
              type="button"
              onClick={() => onSaveFullTranslation(translatedTokens.join(""))}
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
