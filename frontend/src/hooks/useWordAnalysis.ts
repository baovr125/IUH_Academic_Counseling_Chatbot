import { useState, useRef, useCallback } from "react";
import { analyzeWord } from "../services/translationService";

export interface WordAnalysisState {
  isLoading: boolean;
  data: any | null;
  error: string | null;
  selectedText: string;
}

export function useWordAnalysis() {
  const [state, setState] = useState<WordAnalysisState>({
    isLoading: false,
    data: null,
    error: null,
    selectedText: ""
  });
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const analyze = useCallback(async (
    text: string, 
    selectedText: string, 
    sourceLang: string, 
    targetLang: string
  ) => {
    // 1. Cancel previous request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // 2. Create new AbortController
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    
    setState({
      isLoading: true,
      data: null,
      error: null,
      selectedText
    });
    
    try {
      const result = await analyzeWord({
        text,
        selected_text: selectedText,
        source_lang: sourceLang,
        target_lang: targetLang
      }, abortController.signal);
      
      if (!abortController.signal.aborted) {
        if (result.ok) {
          setState({
            isLoading: false,
            data: result.data,
            error: null,
            selectedText
          });
        } else {
          setState({
            isLoading: false,
            data: null,
            error: result.error?.message || "Failed to analyze word",
            selectedText
          });
        }
      }
    } catch (error: any) {
      if (error?.name !== "AbortError") {
        setState({
          isLoading: false,
          data: null,
          error: "Network error",
          selectedText
        });
      }
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState({
      isLoading: false,
      data: null,
      error: null,
      selectedText: ""
    });
  }, []);

  return {
    ...state,
    analyze,
    reset
  };
}
