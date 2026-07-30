// ============================================================================
// IUH Portal AI — Shared API Contracts
// These types define the shape of data exchanged with the future
// FastAPI + PostgreSQL backend. Mock services and real services must both
// resolve to these shapes so UI components never need to change.
// ============================================================================

// ---- Auth ------------------------------------------------------------------

export type UserRole = "student" | "parent" | "highschool" | "guest";

export interface User {
  id: string;
  fullName: string;
  email: string;
  studentCode?: string;
  role: UserRole;
  avatarUrl?: string;
}

export interface LoginPayload {
  identifier: string; // student code or email
  password: string;
  rememberMe?: boolean;
}

export interface RegisterPayload {
  fullName: string;
  identifier: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

// ---- Dashboard ---------------------------------------------------------

export interface LearningStreakDay {
  date: string; // ISO date
  intensity: 0 | 1 | 2 | 3 | 4; // activity level, drives heatmap shade
}

export interface RecentDocument {
  id: string;
  name: string;
  type: "pdf" | "docx" | "xlsx" | "pptx";
  modifiedAt: string;
  category: "notes" | "reports" | "planning";
}

export interface DashboardStats {
  userFullName: string;
  semesterCompletionPercent: number;
  lastSyncedAt: string;
  vocabularyLearnedToday: number;
  gpaScore: number;
  gpaDelta: number;
  creditsEarned: number;
  creditsTotal: number;
  streakDays: number;
  streak: LearningStreakDay[];
  recentDocuments: RecentDocument[];
}

// ---- RAG Chat (Knowledge Hub) -----------------------------------------

export type ChatRole = "user" | "assistant";

export interface Citation {
  id: string;
  sourceTitle: string; // e.g. "Sổ tay sinh viên"
  pageOrSection?: string; // e.g. "trang 15"
  snippet?: string;
  url?: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  /** Raw answer text returned by the RAG pipeline before citation formatting */
  original_answer?: string;
  content: string;
  citations?: Citation[];
  createdAt: string;
  status?: "pending" | "streaming" | "complete" | "error";
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface SendMessagePayload {
  sessionId: string | null;
  content: string;
}

export interface SendMessageResponse {
  sessionId: string;
  message: ChatMessage;
}

// ---- Translation Studio -------------------------------------------------

export type LanguageCode = "vi" | "en" | "de";

export interface TranslateRequest {
  sourceLang: LanguageCode;
  targetLang: LanguageCode;
  sourceText: string;
}

export interface TranslateResponse {
  translatedText: string;
  detectedSourceLang?: LanguageCode;
}

export interface TranslationHistoryItem {
  id: string;
  sourceLang: LanguageCode;
  targetLang: LanguageCode;
  title: string;
  preview: string;
  sourceText: string;
  translatedText: string;
  createdAt: string;
}

// ---- Flashcards / Language Lab ------------------------------------------

export type FlashcardRating = "review_later" | "mastered";

export interface Flashcard {
  id: string;
  term: string;
  partOfSpeech?: string;
  definition: string;
  example?: string;
}

export interface FlashcardSetProgress {
  setId: string;
  setTitle: string;
  currentIndex: number;
  totalCards: number;
  masteredCount: number;
  reviewCount: number;
  recentlyLearned: { term: string; whenLabel: string }[];
  needsReview: { term: string; whenLabel: string }[];
}

// ---- Generic wrapper -----------------------------------------------------

export interface ApiError {
  message: string;
  code?: string;
}

/** Every mock/real service call resolves to this envelope. */
export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };
