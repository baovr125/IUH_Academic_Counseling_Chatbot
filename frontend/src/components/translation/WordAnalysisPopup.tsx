import React, { useEffect, useRef } from "react";

interface MeaningDef {
  pos: string;
  english_definition: string;
  target_language_meaning: string;
  examples: string[];
  target_language_examples: string[];
}

interface WordAnalysisResponse {
  word: string;
  lemma: string;
  part_of_speech: string;
  context: string;
  contextual_meaning?: MeaningDef;
  other_meanings: MeaningDef[];
  cached: boolean;
  latency_ms: number;
}

interface WordAnalysisPopupProps {
  position: { x: number; y: number } | null;
  isLoading: boolean;
  error: string | null;
  data: WordAnalysisResponse | null;
  onClose: () => void;
  onRetry: () => void;
}

const POS_COLORS: Record<string, string> = {
  n: "bg-blue-100 text-blue-700 border-blue-200",
  v: "bg-green-100 text-green-700 border-green-200",
  a: "bg-orange-100 text-orange-700 border-orange-200",
  r: "bg-purple-100 text-purple-700 border-purple-200",
};

const POS_LABELS: Record<string, string> = {
  n: "Noun",
  v: "Verb",
  a: "Adjective",
  r: "Adverb",
  unknown: "Unknown",
};

export const WordAnalysisPopup: React.FC<WordAnalysisPopupProps> = ({
  position,
  isLoading,
  error,
  data,
  onClose,
  onRetry,
}) => {
  const popupRef = useRef<HTMLDivElement>(null);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        popupRef.current && 
        !popupRef.current.contains(target) &&
        !target.closest('#word-analysis-floating-menu')
      ) {
        onClose();
      }
    };
    
    // Slight delay to prevent immediate close on the same click that opened it
    const timer = setTimeout(() => {
      document.addEventListener("mousedown", handleClickOutside);
    }, 100);
    
    return () => {
      clearTimeout(timer);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  if (!position) return null;

  const renderMeaning = (meaning: MeaningDef, isContextual: boolean) => {
    const posCode = meaning.pos || "unknown";
    const posClass = POS_COLORS[posCode] || "bg-gray-100 text-gray-700 border-gray-200";
    const posLabel = POS_LABELS[posCode] || posCode;

    return (
      <div className={`mb-4 pb-4 border-b border-gray-100 last:border-0 last:pb-0 last:mb-0 ${isContextual ? 'bg-amber-50/50 p-2 rounded-md -mx-2' : ''}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className={`px-2 py-0.5 text-xs font-semibold rounded border ${posClass}`}>
            {posLabel}
          </span>
          {isContextual && (
            <span className="text-xs font-medium text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded">
              Context Match
            </span>
          )}
        </div>
        <div className="text-sm font-medium text-gray-900 mb-0.5">
          {meaning.target_language_meaning}
        </div>
        <div className="text-xs text-gray-500 italic mb-2">
          {meaning.english_definition}
        </div>
        
        {meaning.examples && meaning.examples.length > 0 && (
          <div className="pl-3 border-l-2 border-indigo-100 space-y-1">
            {meaning.examples.map((ex, i) => (
              <div key={i}>
                <div className="text-xs text-gray-700">"{ex}"</div>
                {meaning.target_language_examples[i] && (
                  <div className="text-xs text-gray-500">"{meaning.target_language_examples[i]}"</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      ref={popupRef}
      className="fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 w-80 max-w-[90vw] overflow-hidden flex flex-col font-sans transition-all duration-200 ease-in-out"
      style={{
        left: Math.min(position.x, window.innerWidth - 320),
        top: position.y + 10,
        maxHeight: "400px",
      }}
      onMouseDown={(e) => e.preventDefault()} // Prevent text deselect
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 px-4 py-3 flex items-center justify-between border-b border-gray-100">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <span className="text-indigo-600">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </span>
          Word Analysis
        </h3>
        <button 
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content area */}
      <div className="overflow-y-auto flex-1 p-4 custom-scrollbar">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-6 text-gray-400">
            <svg className="animate-spin w-8 h-8 mb-3 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm font-medium animate-pulse">Analyzing context...</p>
          </div>
        )}

        {error && !isLoading && (
          <div className="flex flex-col items-center justify-center py-4 text-center">
            <div className="w-10 h-10 bg-red-100 text-red-500 rounded-full flex items-center justify-center mb-3">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-sm text-red-600 mb-3">{error}</p>
            <button 
              onClick={onRetry}
              className="px-3 py-1.5 bg-red-50 text-red-600 text-sm font-medium rounded-md hover:bg-red-100 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {data && !isLoading && !error && (
          <div>
            <div className="mb-4">
              <div className="flex items-end gap-2 mb-1">
                <h4 className="text-xl font-bold text-gray-900">{data.word}</h4>
                {data.lemma && data.lemma.toLowerCase() !== data.word.toLowerCase() && (
                  <span className="text-sm text-gray-500 mb-0.5">({data.lemma})</span>
                )}
              </div>
            </div>

            {data.contextual_meaning && (
              <div className="mb-4">
                {renderMeaning(data.contextual_meaning, true)}
              </div>
            )}

            {data.other_meanings && data.other_meanings.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Other Meanings</h5>
                {data.other_meanings.map((m, idx) => (
                  <React.Fragment key={idx}>
                    {renderMeaning(m, false)}
                  </React.Fragment>
                ))}
              </div>
            )}
            
            {(!data.contextual_meaning && (!data.other_meanings || data.other_meanings.length === 0)) && (
               <div className="text-center py-4 text-sm text-gray-500">
                 No detailed analysis available for this word.
               </div>
            )}
          </div>
        )}
      </div>
      
      {/* Footer Info */}
      {data && !isLoading && !error && (
        <div className="bg-gray-50 px-4 py-2 border-t border-gray-100 flex justify-between items-center text-[10px] text-gray-400">
          <span>{data.cached ? '⚡ Cached' : 'Powered by WordNet + NLLB'}</span>
          <span>{data.latency_ms}ms</span>
        </div>
      )}
    </div>
  );
};
