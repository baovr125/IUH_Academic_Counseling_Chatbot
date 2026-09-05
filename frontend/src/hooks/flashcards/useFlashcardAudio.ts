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
  const base = env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "";
  return String(base).replace(/\/+$/, "");
};

export function useFlashcardAudio() {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCache = useRef<Map<string, string>>(new Map());
  const playbackSessionRef = useRef<number>(0);

  // Deep teardown of any active HTML5 audio and browser speech synthesis
  const cleanupCurrentAudio = useCallback(() => {
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
  }, []);

  // Prefetch audio and cache as in-memory Blob URL for zero-latency instant playback
  const prefetchAudio = useCallback(async (text?: string, lang: string = "en", phonetic?: string) => {
    const targetText = text?.trim();
    if (!targetText) return;
    const ttsLang = getTTSLangCode(lang);
    const cacheKey = `${ttsLang}_${targetText}_${phonetic || ""}`;
    if (audioCache.current.has(cacheKey)) return;

    try {
      const baseUrl = getApiBaseUrl();
      const phoneticParam = phonetic ? `&phonetic=${encodeURIComponent(phonetic)}` : "";
      const url = `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(targetText)}&lang=${encodeURIComponent(ttsLang)}${phoneticParam}`;
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

  const speakBrowserTTS = useCallback((text: string, lang: string, sessionId: number) => {
    if (sessionId !== playbackSessionRef.current) return;

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
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

      utterance.onend = () => {
        if (playbackSessionRef.current === sessionId) {
          setIsPlayingAudio(false);
        }
      };
      utterance.onerror = () => {
        if (playbackSessionRef.current === sessionId) {
          setIsPlayingAudio(false);
        }
      };
      window.speechSynthesis.speak(utterance);
    } else {
      if (playbackSessionRef.current === sessionId) {
        setIsPlayingAudio(false);
      }
    }
  }, []);

  const playFlashcardServiceTTSFallback = useCallback((text: string, ttsLang: string, sessionId: number) => {
    if (sessionId !== playbackSessionRef.current) return;

    const baseUrl = getApiBaseUrl();
    const fallbackUrl = `${baseUrl}/api/v1/flashcards/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(ttsLang)}`;
    const fallbackAudio = new Audio(fallbackUrl);
    audioRef.current = fallbackAudio;

    fallbackAudio.onended = () => {
      if (playbackSessionRef.current === sessionId) {
        setIsPlayingAudio(false);
      }
    };
    fallbackAudio.onerror = () => {
      if (playbackSessionRef.current === sessionId) {
        speakBrowserTTS(text, ttsLang, sessionId);
      }
    };

    fallbackAudio.play().catch((err: any) => {
      if (err?.name === "AbortError" || playbackSessionRef.current !== sessionId) {
        // User interrupted playback with another click; do not trigger fallback cascade
        return;
      }
      speakBrowserTTS(text, ttsLang, sessionId);
    });
  }, [speakBrowserTTS]);

  const playStreamNeuralTTS = useCallback((text: string, ttsLang: string, phonetic: string | undefined, sessionId: number) => {
    if (!text) {
      if (playbackSessionRef.current === sessionId) {
        setIsPlayingAudio(false);
      }
      return;
    }
    const cacheKey = `${ttsLang}_${text}_${phonetic || ""}`;
    const cachedBlobUrl = audioCache.current.get(cacheKey);
    const baseUrl = getApiBaseUrl();
    const phoneticParam = phonetic ? `&phonetic=${encodeURIComponent(phonetic)}` : "";
    const ttsUrl = cachedBlobUrl || `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(ttsLang)}${phoneticParam}`;

    const audio = new Audio(ttsUrl);
    audioRef.current = audio;

    audio.onended = () => {
      if (playbackSessionRef.current === sessionId) {
        setIsPlayingAudio(false);
      }
    };

    audio.onerror = () => {
      if (playbackSessionRef.current === sessionId) {
        playFlashcardServiceTTSFallback(text, ttsLang, sessionId);
      }
    };

    audio.play().then(() => {
      if (playbackSessionRef.current === sessionId && !cachedBlobUrl) {
        prefetchAudio(text, ttsLang, phonetic);
      }
    }).catch((err: any) => {
      if (err?.name === "AbortError" || playbackSessionRef.current !== sessionId) {
        // User interrupted playback with another click; do not trigger fallback cascade
        return;
      }
      playFlashcardServiceTTSFallback(text, ttsLang, sessionId);
    });
  }, [playFlashcardServiceTTSFallback, prefetchAudio]);

  // Play Audio Pronunciation (Studio-quality Neural Voice via Backend TTS with IPA SSML support)
  const playAudio = useCallback((audioUrl?: string, text?: string, lang: string = "en", phonetic?: string) => {
    cleanupCurrentAudio();
    const sessionId = ++playbackSessionRef.current;
    setIsPlayingAudio(true);

    const targetText = (text || "").trim();
    const ttsLang = getTTSLangCode(lang);
    const baseUrl = getApiBaseUrl();

    // Priority 1: High-precision Microsoft Neural TTS stream (instant 0ms from Blob Cache or backend endpoint)
    if (targetText) {
      playStreamNeuralTTS(targetText, ttsLang, phonetic, sessionId);
      return;
    }

    // Priority 2: Fallback to audioUrl only if text is empty and audioUrl is an external/explicit file
    if (audioUrl && !audioUrl.startsWith("blob:") && audioUrl.length > 5) {
      const fullUrl = audioUrl.startsWith("http")
        ? audioUrl
        : `${baseUrl}${audioUrl.startsWith("/") ? "" : "/"}${audioUrl}`;
      const audio = new Audio(fullUrl);
      audioRef.current = audio;

      audio.onended = () => {
        if (playbackSessionRef.current === sessionId) {
          setIsPlayingAudio(false);
        }
      };
      audio.onerror = () => {
        if (playbackSessionRef.current === sessionId) {
          setIsPlayingAudio(false);
        }
      };

      audio.play().catch((err: any) => {
        if (err?.name === "AbortError" || playbackSessionRef.current !== sessionId) {
          return;
        }
        setIsPlayingAudio(false);
      });
      return;
    }

    setIsPlayingAudio(false);
  }, [cleanupCurrentAudio, playStreamNeuralTTS]);

  const stopAudio = useCallback(() => {
    playbackSessionRef.current++;
    cleanupCurrentAudio();
    setIsPlayingAudio(false);
  }, [cleanupCurrentAudio]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      playbackSessionRef.current++;
      cleanupCurrentAudio();
    };
  }, [cleanupCurrentAudio]);

  return {
    isPlayingAudio,
    playAudio,
    stopAudio,
    prefetchAudio
  };
}
