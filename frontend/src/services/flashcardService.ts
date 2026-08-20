import type { ApiResult, Flashcard, FlashcardRating, FlashcardSetProgress } from "../types";
import { MOCK_FLASHCARD_PROGRESS, MOCK_FLASHCARDS } from "../mock/mockData";
import { getToken } from "./authService";

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "http://localhost:8000").replace(/\/+$/, "");
  if (!base) return endpoint;
  return `${base}${endpoint}`;
};

export async function fetchFlashcardSet(): Promise<
  ApiResult<{ cards: Flashcard[]; progress: FlashcardSetProgress }>
> {
  return { ok: true, data: { cards: MOCK_FLASHCARDS, progress: MOCK_FLASHCARD_PROGRESS } };
}

export async function rateFlashcard(
  cardId: string,
  rating: FlashcardRating
): Promise<ApiResult<{ cardId: string; rating: FlashcardRating }>> {
  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const gradeMap: Record<string, number> = {
      review_later: 2,
      mastered: 5
    };

    await fetch(getApiUrl("/api/v1/flashcards/review"), {
      method: "POST",
      headers,
      body: JSON.stringify({
        card_id: cardId,
        grade: gradeMap[rating] || 3
      }),
    });
  } catch (e) {
    // Fallback if local backend offline
  }

  return { ok: true, data: { cardId, rating } };
}
