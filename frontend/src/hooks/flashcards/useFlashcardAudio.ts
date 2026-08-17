import { useState, useRef, useCallback, useEffect } from "react";

export const getTTSLangCode = (langCode?: string): string => {
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

export const getApiBaseUrl = (): string => {
  const env = (import.meta as any).env || {};
  const base = env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "http://localhost:8000";
  return String(base).replace(/\/+$/, "");
};

export function useFlashcardAudio() {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCache = useRef<Map<string, string>>(new Map());

  // Prefetch audio and cache as in-memory Blob URL for zero-latency instant playback
  const prefetchAudio = useCallback(async (text?: string, lang: string = "en") => {
    const targetText = text?.trim();
    if (!targetText) return;
    const ttsLang = getTTSLangCode(lang);
    const cacheKey = `${ttsLang}_${targetText}`;
    if (audioCache.current.has(cacheKey)) return;

    try {
      const baseUrl = getApiBaseUrl();
      const url = `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(targetText)}&lang=${encodeURIComponent(ttsLang)}`;
      const response = await fetch(url);
      if (response.ok) {
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        audioCache.current.set(cacheKey, objectUrl);
      }
    } catch {
      // Ignore prefetch error silently
    }
  }, []);

  const speakBrowserTTS = useCallback((text: string, lang: string) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const targetLang = getTTSLangCode(lang);
      utterance.lang = targetLang;
      utterance.rate = 0.9;

      const voices = window.speechSynthesis.getVoices();
      const prefix = targetLang.slice(0, 2);
      const voice = voices.find((v) => v.lang.toLowerCase().replace("_", "-").startsWith(prefix)) || null;
      if (voice) {
        utterance.voice = voice;
      }

      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsPlayingAudio(false);
    }
  }, []);

  const playFlashcardServiceTTSFallback = useCallback((text: string, ttsLang: string) => {
    const baseUrl = getApiBaseUrl();
    const fallbackUrl = `${baseUrl}/api/v1/flashcards/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(ttsLang)}`;
    const fallbackAudio = new Audio(fallbackUrl);
    audioRef.current = fallbackAudio;
    fallbackAudio.play().then(() => {
      fallbackAudio.onended = () => setIsPlayingAudio(false);
    }).catch(() => {
      speakBrowserTTS(text, ttsLang);
      setIsPlayingAudio(false);
    });
    fallbackAudio.onerror = () => {
      speakBrowserTTS(text, ttsLang);
      setIsPlayingAudio(false);
    };
  }, [speakBrowserTTS]);

  const playStreamNeuralTTS = useCallback((text: string, ttsLang: string) => {
    if (!text) {
      setIsPlayingAudio(false);
      return;
    }
    const cacheKey = `${ttsLang}_${text}`;
    const cachedBlobUrl = audioCache.current.get(cacheKey);
    const baseUrl = getApiBaseUrl();
    const ttsUrl = cachedBlobUrl || `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(ttsLang)}`;

    const audio = new Audio(ttsUrl);
    audioRef.current = audio;
    audio.play().then(() => {
      audio.onended = () => setIsPlayingAudio(false);
      if (!cachedBlobUrl) {
        prefetchAudio(text, ttsLang);
      }
    }).catch(() => {
      playFlashcardServiceTTSFallback(text, ttsLang);
    });
    audio.onerror = () => {
      playFlashcardServiceTTSFallback(text, ttsLang);
    };
  }, [playFlashcardServiceTTSFallback, prefetchAudio]);

  // Play Audio Pronunciation (Studio-quality Neural Voice via Backend TTS)
  const playAudio = useCallback((audioUrl?: string, text?: string, lang: string = "en") => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlayingAudio(true);

    const targetText = (text || "").trim();
    const ttsLang = getTTSLangCode(lang);
    const baseUrl = getApiBaseUrl();

    // Priority 1: If card already has a generated MP3 URL from MinIO or backend
    if (audioUrl && !audioUrl.startsWith("blob:") && audioUrl.length > 5) {
      const fullUrl = audioUrl.startsWith("http")
        ? audioUrl
        : `${baseUrl}${audioUrl.startsWith("/") ? "" : "/"}${audioUrl}`;
      const audio = new Audio(fullUrl);
      audioRef.current = audio;
      audio.play().then(() => {
        audio.onended = () => setIsPlayingAudio(false);
      }).catch(() => {
        playStreamNeuralTTS(targetText, ttsLang);
      });
      audio.onerror = () => {
        playStreamNeuralTTS(targetText, ttsLang);
      };
      return;
    }

    // Priority 2: Stream Microsoft Edge Neural TTS directly from backend API (or from Blob Cache)
    if (targetText) {
      playStreamNeuralTTS(targetText, ttsLang);
    } else {
      setIsPlayingAudio(false);
    }
  }, [playStreamNeuralTTS]);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlayingAudio(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return {
    isPlayingAudio,
    playAudio,
    stopAudio,
    prefetchAudio
  };
}
