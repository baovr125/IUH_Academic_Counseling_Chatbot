import type { ApiResult, Flashcard, FlashcardRating, FlashcardSetProgress } from "../types";
import { getToken } from "./authService";

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "http://localhost:8000").replace(/\/+$/, "");
  if (!base) return endpoint;
  return `${base}${endpoint}`;
};

export interface BackendDeck {
  id: string;
  user_id?: string;
  title: string;
  description?: string;
  lang_code?: string;
  langCode?: string;
  icon_flag?: string;
  iconFlag?: string;
  cards_count?: number;
  created_at?: string;
}

export interface BackendCardItem {
  id: string;
  deck_id: string;
  term: string;
  definition: string;
  phonetic?: string;
  audio_url?: string;
  example_sentence?: string;
  example?: string;
  part_of_speech?: string;
  partOfSpeech?: string;
  lang_code?: string;
  langCode?: string;
  state?: number;
  stability?: number;
  difficulty?: number;
  due?: string;
  recommended_mode?: "flip" | "spelling";
  cloze_sentence?: string;
}

export interface VerifySpellingResult {
  is_correct: boolean;
  is_close: boolean;
  similarity_score: number;
  correct_term: string;
  user_input: string;
  feedback: string;
  suggested_grade: number;
  audio_url?: string;
  phonetic?: string;
  example_sentence?: string;
  lang_code?: string;
  langCode?: string;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResult<T>> {
  const url = getApiUrl(endpoint);
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      return {
        ok: false,
        error: { message: data?.detail || data?.error?.message || "Lỗi kết nối máy chủ", code: String(response.status) }
      };
    }
    return { ok: true, data: data.data !== undefined ? data.data : data };
  } catch (error: any) {
    return {
      ok: false,
      error: { message: error?.message || "Không thể kết nối tới dịch vụ Flashcard." }
    };
  }
}

// ---- Decks API -------------------------------------------------------------

export async function fetchBackendDecks(): Promise<ApiResult<BackendDeck[]>> {
  return await request<BackendDeck[]>("/api/v1/flashcards/decks", { method: "GET" });
}

export async function createBackendDeck(
  title: string,
  description?: string,
  langCode: string = "en"
): Promise<ApiResult<BackendDeck>> {
  return await request<BackendDeck>("/api/v1/flashcards/decks", {
    method: "POST",
    body: JSON.stringify({ title, description, lang_code: langCode })
  });
}

export async function updateBackendDeck(
  deckId: string,
  payload: { title?: string; description?: string; langCode?: string }
): Promise<ApiResult<BackendDeck>> {
  return await request<BackendDeck>(`/api/v1/flashcards/decks/${deckId}`, {
    method: "PUT",
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      lang_code: payload.langCode
    })
  });
}

export async function deleteBackendDeck(deckId: string): Promise<ApiResult<{ deleted: boolean }>> {
  return await request<{ deleted: boolean }>(`/api/v1/flashcards/decks/${deckId}`, {
    method: "DELETE"
  });
}

// ---- Cards & Study Queue API -----------------------------------------------

export async function fetchStudyQueue(deckId: string, limit: number = 50): Promise<ApiResult<BackendCardItem[]>> {
  return await request<BackendCardItem[]>(`/api/v1/flashcards/decks/${deckId}/study-queue?limit=${limit}`, {
    method: "GET"
  });
}

export async function fetchDeckCards(deckId: string): Promise<ApiResult<BackendCardItem[]>> {
  return await request<BackendCardItem[]>(`/api/v1/flashcards/decks/${deckId}/cards`, {
    method: "GET"
  });
}

export async function createBackendCard(payload: {
  deckId: string;
  term: string;
  definition: string;
  phonetic?: string;
  audioUrl?: string;
  exampleSentence?: string;
  partOfSpeech?: string;
  langCode?: string;
}): Promise<ApiResult<BackendCardItem>> {
  return await request<BackendCardItem>("/api/v1/flashcards/cards", {
    method: "POST",
    body: JSON.stringify({
      deck_id: payload.deckId,
      front_text: payload.term,
      back_text: payload.definition,
      phonetic: payload.phonetic,
      audio_url: payload.audioUrl,
      example_sentence: payload.exampleSentence,
      part_of_speech: payload.partOfSpeech,
      lang_code: payload.langCode || "en"
    })
  });
}

export async function updateBackendCard(
  cardId: string,
  payload: {
    term?: string;
    definition?: string;
    phonetic?: string;
    exampleSentence?: string;
    partOfSpeech?: string;
    langCode?: string;
  }
): Promise<ApiResult<BackendCardItem>> {
  return await request<BackendCardItem>(`/api/v1/flashcards/cards/${cardId}`, {
    method: "PUT",
    body: JSON.stringify({
      front_text: payload.term,
      back_text: payload.definition,
      phonetic: payload.phonetic,
      example_sentence: payload.exampleSentence,
      part_of_speech: payload.partOfSpeech,
      lang_code: payload.langCode
    })
  });
}

// ---- Active Recall Spelling Verification ----------------------------------

export async function verifyCardSpelling(
  cardId: string,
  userInput: string,
  autoApplyReview: boolean = false
): Promise<ApiResult<VerifySpellingResult>> {
  return await request<VerifySpellingResult>(`/api/v1/flashcards/cards/${cardId}/verify-spelling`, {
    method: "POST",
    body: JSON.stringify({
      user_input: userInput,
      auto_apply_review: autoApplyReview
    })
  });
}

// ---- FSRS Review -----------------------------------------------------------

export async function submitFSRSReview(
  cardId: string,
  grade: number // 1: Again, 2: Hard, 3: Good, 4: Easy
): Promise<ApiResult<any>> {
  return await request<any>("/api/v1/flashcards/review", {
    method: "POST",
    body: JSON.stringify({ card_id: cardId, grade })
  });
}

export async function deleteBackendCard(cardId: string): Promise<ApiResult<{ deleted: boolean }>> {
  return await request<{ deleted: boolean }>(`/api/v1/flashcards/cards/${cardId}`, {
    method: "DELETE"
  });
}

// ---- Legacy Compatibility Helpers ------------------------------------------

export async function fetchFlashcardSet(): Promise<
  ApiResult<{ cards: Flashcard[]; progress: FlashcardSetProgress }>
> {
  return {
    ok: true,
    data: {
      cards: [],
      progress: {
        setId: "real_set",
        setTitle: "Sổ từ vựng",
        currentIndex: 0,
        totalCards: 0,
        masteredCount: 0,
        reviewCount: 0,
        recentlyLearned: [],
        needsReview: []
      }
    }
  };
}

export async function rateFlashcard(
  cardId: string,
  rating: FlashcardRating
): Promise<ApiResult<{ cardId: string; rating: FlashcardRating }>> {
  const gradeMap: Record<string, number> = {
    review_later: 2,
    mastered: 4
  };
  await submitFSRSReview(cardId, gradeMap[rating] || 3);
  return { ok: true, data: { cardId, rating } };
}
