import { useEffect } from "react";

interface FlashcardShortcutsProps {
  enabled?: boolean;
  isFlipped?: boolean;
  hasSpellingResult?: boolean;
  onFlip?: () => void;
  onRate?: (grade: number) => void;
  onReplayAudio?: () => void;
  onBack?: () => void;
}

export function useFlashcardShortcuts({
  enabled = true,
  isFlipped = false,
  hasSpellingResult = false,
  onFlip,
  onRate,
  onReplayAudio,
  onBack
}: FlashcardShortcutsProps) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // 1. Guard against input/textarea elements to avoid interfering with spelling test or modals
      const activeTag = document.activeElement?.tagName?.toLowerCase();
      const isInputActive = activeTag === "input" || activeTag === "textarea" || activeTag === "select";

      if (isInputActive) {
        // If in input and user presses Escape, blur input
        if (e.key === "Escape") {
          (document.activeElement as HTMLElement)?.blur();
        }
        return;
      }

      // 2. Space key: Flip card (if in flip mode)
      if (e.code === "Space") {
        e.preventDefault();
        onFlip?.();
        return;
      }

      // 3. Number keys 1, 2, 3, 4: Rate FSRS (if flipped or spelling result is ready)
      if (isFlipped || hasSpellingResult) {
        if (e.key === "1") {
          e.preventDefault();
          onRate?.(1);
          return;
        }
        if (e.key === "2") {
          e.preventDefault();
          onRate?.(2);
          return;
        }
        if (e.key === "3") {
          e.preventDefault();
          onRate?.(3);
          return;
        }
        if (e.key === "4") {
          e.preventDefault();
          onRate?.(4);
          return;
        }
      }

      // 4. Key 'r' / 'R': Replay audio
      if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        onReplayAudio?.();
        return;
      }

      // 5. Escape: Back
      if (e.key === "Escape") {
        e.preventDefault();
        onBack?.();
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled, isFlipped, hasSpellingResult, onFlip, onRate, onReplayAudio, onBack]);
}
