import type { ApiResult, Flashcard, FlashcardRating, FlashcardSetProgress } from "../types";
import { MOCK_FLASHCARD_PROGRESS, MOCK_FLASHCARDS } from "../mock/mockData";
import { delay } from "./utils";

export async function fetchFlashcardSet(): Promise<
  ApiResult<{ cards: Flashcard[]; progress: FlashcardSetProgress }>
> {
  await delay(700);
  return { ok: true, data: { cards: MOCK_FLASHCARDS, progress: MOCK_FLASHCARD_PROGRESS } };
}

export async function rateFlashcard(
  cardId: string,
  rating: FlashcardRating
): Promise<ApiResult<{ cardId: string; rating: FlashcardRating }>> {
  await delay(500);
  return { ok: true, data: { cardId, rating } };
}
