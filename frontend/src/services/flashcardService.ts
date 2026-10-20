import type { ApiResult, Flashcard, FlashcardRating, FlashcardSetProgress } from "../types";
import { getToken } from "./authService";

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "").replace(/\/+$/, "");
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
  /** false = dữ liệu cũ chưa xác nhận ngôn ngữ (không thuộc bộ sưu tập ngôn ngữ nào). */
  lang_confirmed?: boolean;
  is_default?: boolean;
  is_system?: boolean;
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
  recommended_mode?: StudyModeKind;
  cloze_sentence?: string;
  // Hàng đợi học (study-queue)
  choices?: string[] | null;
  is_new?: boolean;
  lapses?: number;
  example_translation?: string | null;
}

export type StudyModeKind = "flip" | "spelling" | "choice" | "listening";

export interface StudyStats {
  total: number;
  new: number;
  due: number;
  learning: number;
  mastered: number;
  weak: number;
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

/** Lấy thông điệp lỗi từ phản hồi backend: {error:{message}} | {detail: string | [{msg}]}. */
export function extractErrorMessage(data: any, fallback: string): string {
  const detail = data?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    return String(first?.msg || first?.message || fallback).replace(/^Value error, /, "");
  }
  return data?.error?.message || fallback;
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
        error: {
          message: extractErrorMessage(data, "Lỗi kết nối máy chủ"),
          code: data?.error?.code || String(response.status),
          data: data?.error?.data
        }
      };
    }
    return { ok: true, data: data.data !== undefined ? data.data : data };
  } catch (error: any) {
    return {
      ok: false,
      error: { message: error?.message || "Không thể kết nối tới dịch vụ Flashcard.", network: true }
    };
  }
}

// ---- Decks API -------------------------------------------------------------

/** Danh sách sổ thẻ; `langCode` lọc ở máy chủ (chỉ sổ của ngôn ngữ đó). */
export async function fetchBackendDecks(langCode?: string): Promise<ApiResult<BackendDeck[]>> {
  const qs = langCode ? `?lang_code=${encodeURIComponent(langCode)}` : "";
  return await request<BackendDeck[]>(`/api/v1/flashcards/decks${qs}`, { method: "GET" });
}

/** Ngôn ngữ là bắt buộc: không còn mặc định "en" ngầm. */
export async function createBackendDeck(
  title: string,
  description: string | undefined,
  langCode: string
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

export async function fetchStudyQueue(
  deckId: string,
  options: { limit?: number; newLimit?: number; weakOnly?: boolean } = {}
): Promise<ApiResult<BackendCardItem[]>> {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 50),
    new_limit: String(options.newLimit ?? 20)
  });
  if (options.weakOnly) params.set("weak_only", "true");
  return await request<BackendCardItem[]>(`/api/v1/flashcards/decks/${deckId}/study-queue?${params.toString()}`, {
    method: "GET"
  });
}

export async function fetchStudyStats(deckId: string): Promise<ApiResult<StudyStats>> {
  return await request<StudyStats>(`/api/v1/flashcards/decks/${deckId}/study-stats`, { method: "GET" });
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
  /** Không bắt buộc: bỏ trống thì thẻ lấy ngôn ngữ của sổ. Khác ngôn ngữ sổ -> 409 LANG_MISMATCH. */
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
      lang_code: payload.langCode || undefined
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

// ---- Excel & CSV Bulk Import -----------------------------------------------

export interface BulkImportResult {
  total_in_file: number;
  inserted: number;
  skipped_duplicates: number;
  cards: BackendCardItem[];
}

export async function importDeckCardsFromExcel(
  deckId: string,
  file: File,
  langCode?: string
): Promise<ApiResult<BulkImportResult>> {
  const queryParam = langCode ? `?lang_code=${encodeURIComponent(langCode)}` : "";
  const url = getApiUrl(`/api/v1/flashcards/decks/${deckId}/import-excel${queryParam}`);
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: formData
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      return {
        ok: false,
        error: { message: extractErrorMessage(data, "Lỗi tải lên file Excel") }
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

export function getExcelTemplateDownloadUrl(): string {
  return getApiUrl("/api/v1/flashcards/template");
}


// ---- AI Vocabulary Generation ----------------------------------------------

export type CefrLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
export type VocabPurpose = "general" | "ielts" | "toeic" | "academic" | "it" | "business";

export interface VocabQuota {
  tier: string;
  tier_label: string;
  limit: number;
  used: number;
  remaining: number;
  resets_at: string;
}

export interface GeneratedVocabItem {
  temp_id: string;
  term: string;
  part_of_speech: string;
  ipa: string;
  definition: string;
  example: string;
  example_translation: string;
  level: string;
  warnings: string[];
  verified: boolean;
}

export interface GenerateVocabResult {
  generation_id: string;
  mode: "topic" | "text" | "image";
  /** Ngôn ngữ của các từ được sinh (en, de, zh, ja, ko, fr, es, ru, th). */
  lang_code?: string;
  topic?: string | null;
  level: CefrLevel;
  requested: number;
  returned: number;
  items: GeneratedVocabItem[];
  dropped: { term: string; reason: string }[];
  providers: string[];
  latency_ms: number;
  quota?: VocabQuota | null;
}

export interface GenerateVocabParams {
  mode: "topic" | "text";
  topic?: string;
  text?: string;
  level: CefrLevel;
  count: number;
  purpose?: VocabPurpose;
  instruction?: string;
  excludeTerms?: string[];
  deckId?: string;
  /** Ngôn ngữ của từ vựng cần sinh; bỏ trống = tiếng Anh. Sổ đích phải cùng ngôn ngữ (409 LANG_MISMATCH). */
  langCode?: string;
}

const GENERATE_TIMEOUT_MS = 90_000;

export async function fetchVocabQuota(): Promise<ApiResult<VocabQuota>> {
  return await request<VocabQuota>("/api/v1/flashcards/vocabulary/quota", { method: "GET" });
}

export async function generateVocabulary(
  params: GenerateVocabParams,
  signal?: AbortSignal
): Promise<ApiResult<GenerateVocabResult>> {
  return await request<GenerateVocabResult>("/api/v1/flashcards/vocabulary/generate", {
    method: "POST",
    signal: signal ?? AbortSignal.timeout(GENERATE_TIMEOUT_MS),
    body: JSON.stringify({
      mode: params.mode,
      topic: params.mode === "topic" ? params.topic : undefined,
      text: params.mode === "text" ? params.text : undefined,
      lang_code: params.langCode || undefined,
      level: params.level,
      count: params.count,
      purpose: params.purpose,
      instruction: params.instruction || undefined,
      exclude_terms: params.excludeTerms ?? [],
      deck_id: params.deckId
    })
  });
}

export async function generateVocabularyFromImage(
  file: File,
  params: Pick<GenerateVocabParams, "level" | "count" | "purpose" | "instruction" | "deckId" | "langCode">,
  signal?: AbortSignal
): Promise<ApiResult<GenerateVocabResult>> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("level", params.level);
  if (params.langCode) formData.append("lang_code", params.langCode);
  formData.append("count", String(params.count));
  if (params.purpose) formData.append("purpose", params.purpose);
  if (params.instruction) formData.append("instruction", params.instruction);
  if (params.deckId) formData.append("deck_id", params.deckId);

  const token = getToken();
  try {
    const response = await fetch(getApiUrl("/api/v1/flashcards/vocabulary/generate-image"), {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
      signal: signal ?? AbortSignal.timeout(GENERATE_TIMEOUT_MS)
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      return {
        ok: false,
        error: {
          message: extractErrorMessage(data, "Không thể trích từ vựng từ ảnh"),
          code: data?.error?.code || String(response.status)
        }
      };
    }
    return { ok: true, data: data.data };
  } catch (error: any) {
    return {
      ok: false,
      error: {
        message:
          error?.name === "TimeoutError"
            ? "AI phản hồi quá lâu. Vui lòng thử lại."
            : error?.message || "Không thể kết nối tới dịch vụ Flashcard."
      }
    };
  }
}

export interface CommitGeneratedParams {
  clientRequestId: string;
  deck?: { title: string; description?: string; langCode: string };
  deckId?: string;
  cards: {
    term: string;
    definition: string;
    partOfSpeech?: string;
    phonetic?: string;
    example?: string;
    exampleTranslation?: string;
    level?: string;
  }[];
  /** `langCode`: ngôn ngữ của các từ được lưu (thêm vào sổ có sẵn mà khác ngôn ngữ của sổ -> 409 LANG_MISMATCH). */
  source: { mode: "topic" | "text" | "image"; topic?: string; level?: CefrLevel; langCode?: string };
}

export interface CommitGeneratedResult extends BulkImportResult {
  deck: BackendDeck;
  extended_saved?: boolean;
  idempotent_replay?: boolean;
}

export async function commitGeneratedVocabulary(
  params: CommitGeneratedParams
): Promise<ApiResult<CommitGeneratedResult>> {
  return await request<CommitGeneratedResult>("/api/v1/flashcards/decks/from-generated", {
    method: "POST",
    body: JSON.stringify({
      client_request_id: params.clientRequestId,
      deck: params.deck
        ? { title: params.deck.title, description: params.deck.description, lang_code: params.deck.langCode }
        : undefined,
      deck_id: params.deckId,
      cards: params.cards.map((c) => ({
        term: c.term,
        definition: c.definition,
        part_of_speech: c.partOfSpeech,
        phonetic: c.phonetic || undefined,
        example: c.example || undefined,
        example_translation: c.exampleTranslation || undefined,
        level: c.level || undefined
      })),
      source: {
        mode: params.source.mode,
        topic: params.source.topic,
        level: params.source.level,
        lang_code: params.source.langCode
      }
    })
  });
}

// ---- Review activity / streak ----------------------------------------------

export interface ReviewStreakData {
  days: { date: string; count: number; intensity: 0 | 1 | 2 | 3 | 4 }[];
  current_streak: number;
  longest_streak: number;
  today_reviews: number;
  /** Số thẻ khác nhau đã ôn hôm nay (today_reviews đếm lượt nên một thẻ ôn nhiều lần bị tính nhiều lần). */
  today_cards?: number;
  total_reviews: number;
}

export async function fetchReviewStreak(days: number = 84): Promise<ApiResult<ReviewStreakData>> {
  return await request<ReviewStreakData>(`/api/v1/flashcards/stats/streak?days=${days}`, { method: "GET" });
}

// ---- Catalog (thư viện bộ từ) ----------------------------------------------

export interface CatalogDeck {
  id: string;
  title: string;
  description?: string;
  lang_code?: string;
  icon_flag?: string;
  category?: string | null;
  level?: string | null;
  slug?: string | null;
  cards_count: number;
  /** Có giá trị nếu người dùng đã thêm bộ này vào sổ của mình (id của sổ đó). */
  added_deck_id?: string | null;
}

export interface CatalogPreviewCard {
  term: string;
  definition: string;
  phonetic?: string | null;
  part_of_speech?: string | null;
  example?: string | null;
  example_translation?: string | null;
}

export interface CatalogCloneResult {
  deck: BackendDeck;
  created: boolean;
  inserted: number;
  skipped_duplicates: number;
}

export async function fetchCatalogDecks(
  filters: { category?: string; level?: string; q?: string } = {}
): Promise<ApiResult<CatalogDeck[]>> {
  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.level) params.set("level", filters.level);
  if (filters.q) params.set("q", filters.q);
  const qs = params.toString();
  return await request<CatalogDeck[]>(`/api/v1/flashcards/catalog/decks${qs ? `?${qs}` : ""}`, { method: "GET" });
}

export async function fetchCatalogPreview(
  deckId: string,
  limit: number = 10
): Promise<ApiResult<{ deck: CatalogDeck; cards: CatalogPreviewCard[] }>> {
  return await request(`/api/v1/flashcards/catalog/decks/${deckId}/preview?limit=${limit}`, { method: "GET" });
}

export async function cloneCatalogDeck(deckId: string): Promise<ApiResult<CatalogCloneResult>> {
  return await request<CatalogCloneResult>(`/api/v1/flashcards/catalog/decks/${deckId}/clone`, { method: "POST" });
}

// ---- Trò chơi ôn từ vựng -----------------------------------------------------------

export type GameKindApi = "match" | "speed" | "builder" | "shooter";
export type GameModeApi = "relax" | "challenge";

export interface GameCardsData {
  game: GameKindApi;
  deck_id: string;
  lang_code: string | null;
  playable: boolean;
  reason: string | null;
  min_required: number;
  total_cards: number;
  due_count: number;
  cards: {
    id: string;
    term: string;
    definition: string;
    phonetic?: string | null;
    audio_url?: string | null;
    part_of_speech?: string | null;
    lang_code: string;
    is_due: boolean;
    choices?: string[];
  }[];
}

export interface GameLevel {
  level: number;
  xp: number;
  level_floor_xp: number;
  next_level_xp: number;
}

export interface GameBest {
  score: number;
  stars: number;
  best_combo: number;
}

export interface GameStats {
  lang_code: string | null;
  level: GameLevel;
  plays_total: number;
  plays_today: number;
  games: Record<GameKindApi, { plays: number; last_played: string | null; best: Record<GameModeApi, GameBest | null> }>;
}

export interface GameSessionRecord {
  id: string;
  game: GameKindApi;
  mode: GameModeApi;
  total: number;
  correct: number;
  mistakes: number;
  hints: number;
  best_combo: number;
  duration_ms: number;
  score: number;
  stars: number;
  xp: number;
  applied_review: boolean;
  reviewed_count: number;
}

export interface GameSessionResponse {
  session: GameSessionRecord;
  is_record: boolean;
  previous_best?: number;
  review_eligible?: number;
  ignored_items?: number;
  idempotent_replay: boolean;
  level: GameLevel | null;
}

export interface SubmitGameSessionParams {
  clientRequestId: string;
  game: GameKindApi;
  mode: GameModeApi;
  deckId: string;
  durationMs: number;
  items: { card_id: string; correct: boolean; attempts: number; hints: number }[];
  applyReview: boolean;
}

export async function fetchGameCards(game: GameKindApi, deckId: string, count?: number): Promise<ApiResult<GameCardsData>> {
  const params = new URLSearchParams({ deck_id: deckId });
  if (count) params.set("count", String(count));
  return await request<GameCardsData>(`/api/v1/flashcards/games/${game}/cards?${params.toString()}`, { method: "GET" });
}

export async function submitGameSession(params: SubmitGameSessionParams): Promise<ApiResult<GameSessionResponse>> {
  return await request<GameSessionResponse>("/api/v1/flashcards/games/sessions", {
    method: "POST",
    body: JSON.stringify({
      client_request_id: params.clientRequestId,
      game: params.game,
      mode: params.mode,
      deck_id: params.deckId,
      duration_ms: Math.max(0, Math.round(params.durationMs)),
      items: params.items,
      apply_review: params.applyReview
    })
  });
}

export async function fetchGameStats(langCode?: string): Promise<ApiResult<GameStats>> {
  const qs = langCode ? `?lang_code=${encodeURIComponent(langCode)}` : "";
  return await request<GameStats>(`/api/v1/flashcards/games/stats${qs}`, { method: "GET" });
}

// ---- Bộ sưu tập theo ngôn ngữ (10 ngôn ngữ) ----------------------------------

export interface LanguageSummaryItem {
  code: string;
  learnable: boolean;
  decks: number;
  cards: number;
  new: number;
  due: number;
  /** Số thẻ đã thuộc (không còn mới và độ bền trí nhớ >= 21 ngày). Máy chủ cũ chưa trả trường này. */
  mastered?: number;
  weak: number;
  last_activity?: string | null;
  default_deck_id?: string | null;
}

export interface UnconfirmedDeck {
  id: string;
  title: string;
  lang_code?: string | null;
  cards_count: number;
}

export interface LanguageSummary {
  languages: LanguageSummaryItem[];
  unconfirmed: { decks: UnconfirmedDeck[]; cards: number };
}

export type LanguageCardSort = "recent" | "alpha" | "due";
export type LanguageCardStatus = "all" | "new" | "due" | "weak";

export interface LanguageCardItem extends BackendCardItem {
  deck_title?: string;
  target_lang?: string;
  created_at?: string;
}

export interface LanguageCardsPage {
  items: LanguageCardItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface LanguageCardsQuery {
  q?: string;
  sort?: LanguageCardSort;
  status?: LanguageCardStatus;
  deckId?: string;
  limit?: number;
  offset?: number;
}

export async function fetchLanguageSummary(): Promise<ApiResult<LanguageSummary>> {
  return await request<LanguageSummary>("/api/v1/flashcards/languages", { method: "GET" });
}

export async function fetchLanguageCards(
  langCode: string,
  query: LanguageCardsQuery = {}
): Promise<ApiResult<LanguageCardsPage>> {
  const params = new URLSearchParams();
  if (query.q?.trim()) params.set("q", query.q.trim());
  if (query.sort) params.set("sort", query.sort);
  if (query.status && query.status !== "all") params.set("status", query.status);
  if (query.deckId) params.set("deck_id", query.deckId);
  params.set("limit", String(query.limit ?? 50));
  params.set("offset", String(query.offset ?? 0));
  return await request<LanguageCardsPage>(
    `/api/v1/flashcards/languages/${encodeURIComponent(langCode)}/cards?${params.toString()}`,
    { method: "GET" }
  );
}

/** Xác nhận/đổi ngôn ngữ của cả sổ (mọi thẻ đổi theo) — dùng cho mục "Cần xác nhận ngôn ngữ". */
export async function setDeckLanguage(deckId: string, langCode: string): Promise<ApiResult<BackendDeck>> {
  return await request<BackendDeck>(`/api/v1/flashcards/decks/${deckId}/language`, {
    method: "POST",
    body: JSON.stringify({ lang_code: langCode })
  });
}

export interface SaveFromTranslationParams {
  clientRequestId: string;
  /** Ngôn ngữ của `term`. Bắt buộc: thiếu/không rõ -> backend trả 422 LANG_REQUIRED. */
  sourceLang: string;
  term: string;
  /** Nghĩa tiếng Việt. */
  translation: string;
  phonetic?: string;
  example?: string;
  exampleTranslation?: string;
  partOfSpeech?: string;
  deckId?: string;
  onDuplicate?: "reject" | "update";
  detection?: { status?: string; engine?: string; confidence?: number };
}

export interface SaveFromTranslationResult {
  created: boolean;
  updated?: boolean;
  idempotent_replay?: boolean;
  card: BackendCardItem;
  deck: BackendDeck;
}

export async function saveCardFromTranslation(
  params: SaveFromTranslationParams
): Promise<ApiResult<SaveFromTranslationResult>> {
  return await request<SaveFromTranslationResult>("/api/v1/flashcards/cards/from-translation", {
    method: "POST",
    body: JSON.stringify({
      client_request_id: params.clientRequestId,
      source_lang: params.sourceLang,
      target_lang: "vi",
      term: params.term,
      translation: params.translation,
      phonetic: params.phonetic || undefined,
      example: params.example || undefined,
      example_translation: params.exampleTranslation || undefined,
      part_of_speech: params.partOfSpeech || undefined,
      deck_id: params.deckId || undefined,
      on_duplicate: params.onDuplicate ?? "reject",
      detection: params.detection
    })
  });
}
