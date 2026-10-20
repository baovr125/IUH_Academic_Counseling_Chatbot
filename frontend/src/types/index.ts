// ============================================================================
// IUH Portal AI — Shared API Contracts
// These types define the shape of data exchanged with the future
// FastAPI + PostgreSQL backend. Mock services and real services must both
// resolve to these shapes so UI components never need to change.
// ============================================================================

// ---- Auth ------------------------------------------------------------------

export type UserRole = "student" | "public" | "admin";

export interface User {
  id: string;
  fullName: string;
  email: string;
  studentCode?: string | null;
  department?: string | null;
  major?: string | null;
  phoneNumber?: string | null;
  role: UserRole;
  avatarUrl?: string | null;
  /** Tài khoản đã có mật khẩu đăng nhập trực tiếp (server không bao giờ gửi hash). */
  hasPassword?: boolean;
  googleId?: string | null;
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
  userType?: "student" | "public";
  department?: string;
  major?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface ChangePasswordPayload {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

/** Các trường hồ sơ được phép sửa (email, MSSV và vai trò chỉ đọc). */
export interface UpdateProfilePayload {
  fullName?: string;
  phoneNumber?: string;
  department?: string;
  major?: string;
  avatarUrl?: string;
}

// ---- User Settings ---------------------------------------------------------

export interface UserSettings {
  theme: "light" | "dark" | "system";
  language: "vi" | "en";
  soundEnabled: boolean;
  academicAlerts: boolean;
}

export interface UpdateSettingsPayload {
  theme?: "light" | "dark" | "system";
  language?: "vi" | "en";
  soundEnabled?: boolean;
  academicAlerts?: boolean;
}

// ---- Dashboard ---------------------------------------------------------

export interface LearningStreakDay {
  date: string; // ISO date
  intensity: 0 | 1 | 2 | 3 | 4; // activity level, drives heatmap shade
  count?: number;
}

export interface RecentDocument {
  id: string;
  name: string;
  type: "pdf" | "docx" | "xlsx" | "pptx";
  modifiedAt: string;
  category: "notes" | "reports" | "planning" | "research" | "handbook";
  pageCount?: number;
  fileSize?: string;
  status?: "completed" | "processing" | "ready";
  translatedTitle?: string;
}

export interface RecentChatPreview {
  id: string;
  title: string;
  lastMessage: string;
  updatedAt: string;
  messageCount: number;
}

export interface AcademicDeadline {
  id: string;
  title: string;
  date: string;
  daysRemaining?: number;
  type: "urgent" | "warning" | "info" | "success";
  tag: string;
  link?: string;
}

export interface AdmissionNews {
  id: string;
  title: string;
  date: string;
  badge: string;
  description: string;
  link?: string;
}

export interface PublicUserProductivity {
  totalDocsTranslated: number;
  totalPagesProcessed: number;
  timeSavedHours: number;
}

export interface DashboardStats {
  userFullName: string;
  role?: UserRole;
  studentCode?: string;
  department?: string;
  major?: string;
  semesterName?: string;
  currentWeek?: number;
  semesterCompletionPercent: number;
  lastSyncedAt: string;
  gpaScore: number;
  gpaDelta: number;
  creditsEarned: number;
  creditsTotal: number;
  streakDays: number;
  streak: LearningStreakDay[];
  /** "live": streak/heatmap lấy từ nhật ký ôn tập thật; "sample": dữ liệu mẫu (khách, hoặc không tải được). */
  streakSource: "live" | "sample";
  recentDocuments: RecentDocument[];
  recentChatSessions?: RecentChatPreview[];
  academicDeadlines: AcademicDeadline[];
  publicProductivity?: PublicUserProductivity;
  admissionNews?: AdmissionNews[];
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
  bypassCache?: boolean;
  citations?: Citation[];
  createdAt: string;
  status?: "pending" | "streaming" | "complete" | "error";
  cacheStatus?: "HIT" | "MISS" | "UNKNOWN";
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
  bypassCache?: boolean;
}

export interface SendMessageResponse {
  sessionId: string;
  message: ChatMessage;
}

// ---- Translation Studio -------------------------------------------------

export type LanguageCode = "vi" | "en" | "de" | "zh" | "ja" | "ko" | "fr" | "es" | "ru" | "th" | string;

export interface TranslateRequest {
  sourceLang: LanguageCode;
  targetLang: LanguageCode;
  sourceText: string;
  domain?: string;
  /** Ngôn ngữ đã nhận diện ở lần trước; chỉ gửi khi sourceLang = "auto" để nhãn ổn định khi đang gõ. */
  sourceLangHint?: LanguageCode;
}

export interface DetectionCandidate {
  language: string;
  confidence: number;
}

export type DetectionStatus = "detected" | "uncertain" | "unknown" | "unsupported" | "invalid_input" | "system_error";

export type DetectionReason =
  | "short_input"
  | "low_confidence"
  | "engines_disagree"
  | "out_of_scope"
  | "script_mismatch"
  | "mixed_language";

/** Mã lỗi backend trả về khi KHÔNG dịch vì ngôn ngữ nguồn chưa xác định được. */
export const LANGUAGE_STOP_CODES = ["LANG_UNCERTAIN", "LANG_UNSUPPORTED", "LANG_UNKNOWN", "INVALID_INPUT"] as const;

export interface LanguageDetectionDetails {
  /** Chỉ có giá trị khi status = "detected" (hoặc ngôn ngữ do người dùng chọn thủ công). */
  resolved_source_lang?: LanguageCode | null;
  status: DetectionStatus;
  confidence: number;
  margin: number;
  engine: "fusion" | "fasttext" | "lingua" | "script" | "hint" | "manual" | "none" | string;
  /** Tối đa 3 ngôn ngữ được hỗ trợ có khả năng cao nhất (dùng cho UI chọn ngôn ngữ). */
  candidates?: DetectionCandidate[];
  is_multilingual?: boolean;
  message?: string | null;
  reason?: DetectionReason | null;
  /** Với status = "unsupported": ngôn ngữ thực tế được nhận ra (vd "it", "ar"). */
  detected_language?: string | null;
}

export type WarningSeverity = "info" | "warning" | "error";

export interface DomainCandidate {
  domain: string;
  term?: string | null;
  translation?: string | null;
}

/** Kết quả chọn/nhận diện chuyên ngành (chế độ dịch bằng LLM). */
export interface DomainDetails {
  /** selected: người dùng chọn thủ công | detected | ambiguous | unknown | error | skipped */
  status: "selected" | "detected" | "ambiguous" | "unknown" | "error" | "skipped" | string;
  domain?: string | null;
  confidence: number;
  method: "manual" | "exact" | "llm" | "lexical_llm" | "none" | string;
  matched_terms?: string[];
  applied_terms?: string[];
  /** Với status = "ambiguous": các domain cùng chứa thuật ngữ (UI cho người dùng chọn). */
  candidates?: DomainCandidate[];
  reason?: string | null;
  /** Nguồn bản dịch: "dictionary" | "nllb" | "llm:<provider>:<model>". */
  translator?: string | null;
}

/** Cảnh báo có cấu trúc từ backend; UI gộp theo `code`. */
export interface TranslationWarning {
  code: string;
  severity: WarningSeverity;
  message: string;
  domain?: string | null;
  candidates?: DomainCandidate[];
}

export interface TranslateResponse {
  translatedText: string;
  detectedSourceLang?: LanguageCode;
  detection?: LanguageDetectionDetails;
  domainDetails?: DomainDetails;
  warnings?: TranslationWarning[];
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
  phonetic?: string;
  audio_url?: string;
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

// ---- Analytics -------------------------------------------------------------

export interface AnalyticsData {
  metrics: {
    avg_latency_ms: number;
    total_prompt_tokens: number;
    satisfaction_rate: number;
    total_feedback: number;
    like_count: number;
    dislike_count: number;
  };
  top_queries: { query: string; count: number }[];
}

export interface ApiErrorDetail {
  field: string;
  message: string;
  type?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  field?: string;
  details?: ApiErrorDetail[];
  /** Dữ liệu kèm theo của lỗi nghiệp vụ (vd DUPLICATE_CARD kèm thẻ đã có). */
  data?: any;
  /** true = không nhận được phản hồi HTTP nào (mất mạng / máy chủ không chạy). */
  network?: boolean;
  /** Có khi lỗi đến từ bước nhận diện ngôn ngữ nguồn (LANG_* / INVALID_INPUT). */
  detection?: LanguageDetectionDetails;
}

/** Every mock/real service call resolves to this envelope. */
export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };
