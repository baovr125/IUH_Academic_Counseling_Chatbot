import { useCallback, useEffect, useState } from "react";
import * as translationService from "../services/translationService";
import type { LanguageCode, TranslationHistoryItem } from "../types";

interface UseTranslationReturn {
  sourceLang: LanguageCode;
  targetLang: LanguageCode;
  sourceText: string;
  translatedText: string;
  isTranslating: boolean;
  isSaving: boolean;
  history: TranslationHistoryItem[];
  isLoadingHistory: boolean;
  error: string | null;
  setSourceLang: (lang: LanguageCode) => void;
  setTargetLang: (lang: LanguageCode) => void;
  setSourceText: (text: string) => void;
  swapLanguages: () => void;
  translate: () => Promise<void>;
  saveCurrentTranslation: () => Promise<void>;
  removeHistoryItem: (id: string) => Promise<void>;
  clearAllHistory: () => Promise<void>;
}

export function useTranslation(): UseTranslationReturn {
  const [sourceLang, setSourceLang] = useState<LanguageCode>("en");
  const [targetLang, setTargetLang] = useState<LanguageCode>("vi");
  const [sourceText, setSourceText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [history, setHistory] = useState<TranslationHistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    const result = await translationService.fetchTranslationHistory();
    setIsLoadingHistory(false);
    if (result.ok) setHistory(result.data);
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const swapLanguages = useCallback(() => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setSourceText(translatedText);
    setTranslatedText(sourceText);
  }, [sourceLang, targetLang, sourceText, translatedText]);

  const translate = useCallback(async () => {
    setError(null);
    setIsTranslating(true);
    const result = await translationService.translateText({ sourceLang, targetLang, sourceText });
    setIsTranslating(false);

    if (!result.ok) {
      setError(result.error.message);
      return;
    }
    setTranslatedText(result.data.translatedText);
  }, [sourceLang, targetLang, sourceText]);

  const saveCurrentTranslation = useCallback(async () => {
    if (!sourceText || !translatedText) return;
    setIsSaving(true);
    await translationService.saveTranslation({ sourceLang, targetLang, sourceText, translatedText });
    setIsSaving(false);
    loadHistory();
  }, [sourceLang, targetLang, sourceText, translatedText, loadHistory]);

  const removeHistoryItem = useCallback(async (id: string) => {
    await translationService.deleteTranslationHistoryItem(id);
    setHistory((prev) => prev.filter((h) => h.id !== id));
  }, []);

  const clearAllHistory = useCallback(async () => {
    await translationService.clearTranslationHistory();
    setHistory([]);
  }, []);

  return {
    sourceLang,
    targetLang,
    sourceText,
    translatedText,
    isTranslating,
    isSaving,
    history,
    isLoadingHistory,
    error,
    setSourceLang,
    setTargetLang,
    setSourceText,
    swapLanguages,
    translate,
    saveCurrentTranslation,
    removeHistoryItem,
    clearAllHistory,
  };
}
