import { useCallback, useEffect, useState } from "react";
import * as flashcardService from "../services/flashcardService";
import type { Flashcard, FlashcardRating, FlashcardSetProgress } from "../types";

export function useFlashcards() {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [progress, setProgress] = useState<FlashcardSetProgress | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRating, setIsRating] = useState(false);

  useEffect(() => {
    (async () => {
      setIsLoading(true);
      const result = await flashcardService.fetchFlashcardSet();
      setIsLoading(false);
      if (result.ok) {
        setCards(result.data.cards);
        setProgress(result.data.progress);
        setCurrentIndex(result.data.progress.currentIndex);
      }
    })();
  }, []);

  const flip = useCallback(() => setIsFlipped((f) => !f), []);

  const rate = useCallback(
    async (rating: FlashcardRating) => {
      const card = cards[currentIndex % cards.length];
      if (!card) return;
      setIsRating(true);
      await flashcardService.rateFlashcard(card.id, rating);
      setIsRating(false);
      setIsFlipped(false);
      setCurrentIndex((i) => i + 1);
    },
    [cards, currentIndex]
  );

  return {
    currentCard: cards[currentIndex % (cards.length || 1)],
    progress,
    currentIndex,
    isFlipped,
    isLoading,
    isRating,
    flip,
    rate,
  };
}
