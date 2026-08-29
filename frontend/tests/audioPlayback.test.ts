import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFlashcardAudio, getTTSLangCode } from "../src/hooks/flashcards/useFlashcardAudio";

describe("Audio Playback and Spam-Click Prevention Tests", () => {
  let createdAudios: any[] = [];
  let mockSpeechSynthesis: any;

  beforeEach(() => {
    createdAudios = [];

    // Mock HTMLMediaElement / Audio constructor using class
    class MockAudio {
      url: string;
      src: string;
      currentTime: number;
      paused: boolean;
      onended: (() => void) | null;
      onerror: (() => void) | null;
      oncanplay: (() => void) | null;
      play: any;
      pause: any;
      removeAttribute: any;
      load: any;

      constructor(url: string) {
        this.url = url;
        this.src = url;
        this.currentTime = 0;
        this.paused = false;
        this.onended = null;
        this.onerror = null;
        this.oncanplay = null;
        this.play = vi.fn().mockImplementation(() => Promise.resolve());
        this.pause = vi.fn().mockImplementation(() => {
          this.paused = true;
        });
        this.removeAttribute = vi.fn();
        this.load = vi.fn();
        createdAudios.push(this);
      }
    }

    vi.stubGlobal("Audio", MockAudio);

    // Mock window.speechSynthesis
    mockSpeechSynthesis = {
      speak: vi.fn(),
      cancel: vi.fn(),
      getVoices: vi.fn().mockReturnValue([]),
    };
    vi.stubGlobal("speechSynthesis", mockSpeechSynthesis);

    class MockSpeechSynthesisUtterance {
      text: string;
      lang: string;
      rate: number;
      voice: any;
      onend: any;
      onerror: any;
      constructor(text: string) {
        this.text = text;
        this.lang = "en-US";
        this.rate = 1;
        this.voice = null;
        this.onend = null;
        this.onerror = null;
      }
    }
    vi.stubGlobal("SpeechSynthesisUtterance", MockSpeechSynthesisUtterance);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("maps language codes correctly to TTS voices", () => {
    expect(getTTSLangCode("en")).toBe("en-US");
    expect(getTTSLangCode("vi")).toBe("vi-VN");
    expect(getTTSLangCode("fr")).toBe("fr-FR");
    expect(getTTSLangCode("ja")).toBe("ja-JP");
    expect(getTTSLangCode("zh")).toBe("zh-CN");
    expect(getTTSLangCode("unknown")).toBe("en-US");
  });

  it("plays audio and manages isPlayingAudio state", async () => {
    const { result } = renderHook(() => useFlashcardAudio());

    expect(result.current.isPlayingAudio).toBe(false);

    act(() => {
      result.current.playAudio(undefined, "computer", "en");
    });

    expect(result.current.isPlayingAudio).toBe(true);
    expect(createdAudios.length).toBe(1);
    expect(createdAudios[0].url).toContain("/api/v1/translate/tts");
    expect(createdAudios[0].url).toContain("computer");

    // Simulate audio finished playing
    act(() => {
      if (createdAudios[0].onended) {
        createdAudios[0].onended();
      }
    });

    expect(result.current.isPlayingAudio).toBe(false);
  });

  it("handles rapid spam clicks cleanly without triggering fallback cascade", async () => {
    const { result } = renderHook(() => useFlashcardAudio());

    // Click 1: User clicks "software"
    act(() => {
      result.current.playAudio(undefined, "software", "en");
    });

    const firstAudio = createdAudios[0];
    expect(firstAudio).toBeDefined();

    // Click 2: User rapidly clicks "hardware" 50ms later
    act(() => {
      result.current.playAudio(undefined, "hardware", "en");
    });

    const secondAudio = createdAudios[1];
    expect(secondAudio).toBeDefined();
    expect(secondAudio.url).toContain("hardware");

    // First audio must have been paused and cleaned up
    expect(firstAudio.pause).toHaveBeenCalled();

    // Simulate AbortError on first audio catch handler
    const abortErr = new DOMException("The play() request was interrupted", "AbortError");
    // Crucial check: AbortError from first audio MUST NOT trigger SpeechSynthesis or fallback cascade
    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();

    // Click 3: User rapidly clicks "network"
    act(() => {
      result.current.playAudio(undefined, "network", "en");
    });

    const thirdAudio = createdAudios[2];
    expect(thirdAudio).toBeDefined();
    expect(thirdAudio.url).toContain("network");

    // Speech synthesis still not triggered because aborts were filtered out
    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();
    expect(result.current.isPlayingAudio).toBe(true);

    // Only when the latest active audio finishes, state becomes idle
    act(() => {
      if (thirdAudio.onended) {
        thirdAudio.onended();
      }
    });

    expect(result.current.isPlayingAudio).toBe(false);
  });

  it("stops both HTML5 Audio and window.speechSynthesis when stopAudio is invoked", () => {
    const { result } = renderHook(() => useFlashcardAudio());

    act(() => {
      result.current.playAudio(undefined, "algorithm", "en");
    });

    expect(result.current.isPlayingAudio).toBe(true);
    const activeAudio = createdAudios[0];

    act(() => {
      result.current.stopAudio();
    });

    expect(result.current.isPlayingAudio).toBe(false);
    expect(activeAudio.pause).toHaveBeenCalled();
    expect(mockSpeechSynthesis.cancel).toHaveBeenCalled();
  });

  it("triggers fallback TTS when a genuine network error occurs on the active session", async () => {
    const { result } = renderHook(() => useFlashcardAudio());

    act(() => {
      result.current.playAudio(undefined, "database", "en");
    });

    const primaryAudio = createdAudios[0];
    expect(primaryAudio).toBeDefined();

    // Simulate genuine non-abort error (e.g. backend TTS service 503)
    act(() => {
      if (primaryAudio.onerror) {
        primaryAudio.onerror();
      }
    });

    // Should create secondary fallback audio instance pointing to /api/v1/flashcards/tts
    expect(createdAudios.length).toBe(2);
    const fallbackAudio = createdAudios[1];
    expect(fallbackAudio.url).toContain("/api/v1/flashcards/tts");

    // If fallback also encounters genuine error, fallback to browser SpeechSynthesis
    act(() => {
      if (fallbackAudio.onerror) {
        fallbackAudio.onerror();
      }
    });

    expect(mockSpeechSynthesis.speak).toHaveBeenCalledTimes(1);
  });
});
