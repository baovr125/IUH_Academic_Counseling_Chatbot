import type {
  ChatSession,
  DashboardStats,
  Flashcard,
  FlashcardSetProgress,
  TranslationHistoryItem,
  User,
} from "../types";

export const MOCK_USER: User = {
  id: "u_001",
  fullName: "Nguyễn Văn A",
  email: "nguyenvana@iuh.edu.vn",
  studentCode: "20045211",
  role: "student",
};

export const MOCK_DASHBOARD_STATS: DashboardStats = {
  userFullName: MOCK_USER.fullName,
  semesterCompletionPercent: 85,
  lastSyncedAt: "2 mins ago",
  vocabularyLearnedToday: 124,
  gpaScore: 3.85,
  gpaDelta: 0.12,
  creditsEarned: 18,
  creditsTotal: 24,
  streakDays: 24,
  streak: Array.from({ length: 84 }, (_, i) => ({
    date: new Date(Date.now() - (83 - i) * 86400000).toISOString(),
    intensity: [0, 1, 2, 3, 4][Math.floor(Math.random() * 5)] as 0 | 1 | 2 | 3 | 4,
  })),
  recentDocuments: [
    { id: "d1", name: "Quantum Mechanics Notes.pdf", type: "pdf", modifiedAt: "Oct 24, 2023", category: "notes" },
    { id: "d2", name: "Lab Report #4.docx", type: "docx", modifiedAt: "Oct 22, 2023", category: "reports" },
    { id: "d3", name: "Study Schedule.xlsx", type: "xlsx", modifiedAt: "Oct 19, 2023", category: "planning" },
  ],
};

export const MOCK_CHAT_SESSIONS: ChatSession[] = [
  {
    id: "s_today_1",
    title: "Student Handbook Rules",
    updatedAt: new Date().toISOString(),
    messages: [
      {
        id: "m1",
        role: "user",
        content: "Can you summarize the main rules for applying for a leave of absence?",
        createdAt: new Date().toISOString(),
        status: "complete",
      },
      {
        id: "m2",
        role: "assistant",
        original_answer:
          "According to the regulations, a leave of absence requires: submission at least 3 days in advance, approval from the academic advisor or department head, and valid documentation for leaves exceeding 5 days.",
        content:
          "According to the regulations, a leave of absence requires the following:\n\n- Submission of a formal request at least 3 days in advance.\n- Approval from the direct academic advisor or department head.\n- Valid documentation (e.g., medical certificate) for leaves exceeding 5 days.",
        citations: [
          {
            id: "c1",
            sourceTitle: "Sổ tay sinh viên",
            pageOrSection: "trang 15",
          },
        ],
        createdAt: new Date().toISOString(),
        status: "complete",
      },
    ],
  },
  {
    id: "s_today_2",
    title: "Leave Application Email",
    updatedAt: new Date(Date.now() - 3600_000).toISOString(),
    messages: [],
  },
  {
    id: "s_yesterday_1",
    title: "Financial Report Q3 Analysis",
    updatedAt: new Date(Date.now() - 86400_000).toISOString(),
    messages: [],
  },
];

export const MOCK_TRANSLATION_HISTORY: TranslationHistoryItem[] = [
  {
    id: "t1",
    sourceLang: "vi",
    targetLang: "en",
    title: "Đề cương chi tiết học phần: Trí tuệ nhân tạo",
    preview: "Xin chào, tôi muốn dịch tài liệu này sang tiếng Anh để nộp cho giảng viên hướng dẫn về đề tài nghiên cứu khoa học...",
    sourceText: "Xin chào, tôi muốn dịch tài liệu này sang tiếng Anh để nộp cho giảng viên hướng dẫn về đề tài nghiên cứu khoa học.",
    translatedText: "Hello, I would like to translate this document into English to submit to my academic advisor regarding the research topic.",
    createdAt: "2 hours ago",
  },
  {
    id: "t2",
    sourceLang: "en",
    targetLang: "vi",
    title: "AI Implementation in Modern Portals",
    preview: "The implementation of artificial intelligence in modern portals requires a deep understanding of user experience and backend scalability...",
    sourceText: "The implementation of artificial intelligence in modern portals requires a deep understanding of user experience and backend scalability.",
    translatedText: "Việc triển khai trí tuệ nhân tạo trong các cổng thông tin hiện đại đòi hỏi sự hiểu biết sâu sắc về trải nghiệm người dùng và khả năng mở rộng hệ thống.",
    createdAt: "Yesterday",
  },
  {
    id: "t3",
    sourceLang: "vi",
    targetLang: "en",
    title: "Báo cáo thực tập tốt nghiệp - IUH",
    preview: "Tài liệu này bao gồm phần giới thiệu về công ty thực tập và các công nghệ đã áp dụng trong quá trình làm việc tại doanh nghiệp...",
    sourceText: "Tài liệu này bao gồm phần giới thiệu về công ty thực tập và các công nghệ đã áp dụng trong quá trình làm việc tại doanh nghiệp.",
    translatedText: "This document includes an introduction to the internship company and the technologies applied while working at the enterprise.",
    createdAt: "Oct 24, 2023",
  },
];

// Tiny VI -> DE phrase table so the demo translation feels real for the
// example the requester gave ("tôi muốn đăng ký tín chỉ").
const VI_DE_PHRASES: Record<string, string> = {
  "tôi muốn đăng ký tín chỉ": "Ich möchte mich für Kreditpunkte anmelden.",
  "chào bạn": "Hallo!",
  "cảm ơn bạn": "Danke schön.",
};

export function mockTranslate(sourceText: string, targetLang: "de" | "en" | "vi"): string {
  const key = sourceText.trim().toLowerCase();
  if (targetLang === "de" && VI_DE_PHRASES[key]) return VI_DE_PHRASES[key];
  if (targetLang === "de") {
    return `[DE] ${sourceText} (übersetzt)`;
  }
  if (targetLang === "en") {
    return `[EN] ${sourceText} (translated)`;
  }
  return `[VI] ${sourceText} (đã dịch)`;
}

export const MOCK_FLASHCARDS: Flashcard[] = [
  { id: "f1", term: "Implementation", partOfSpeech: "noun", definition: "Sự triển khai, thực hiện một kế hoạch hoặc hệ thống.", example: "The implementation of the new system took three months." },
  { id: "f2", term: "Threshold", partOfSpeech: "noun", definition: "Ngưỡng, giới hạn bắt đầu của một trạng thái.", example: "The signal must exceed a certain threshold." },
  { id: "f3", term: "Infrastructure", partOfSpeech: "noun", definition: "Cơ sở hạ tầng.", example: "The university invested in digital infrastructure." },
];

export const MOCK_FLASHCARD_PROGRESS: FlashcardSetProgress = {
  setId: "set_vocab_1",
  setTitle: "Language Lab: Vocabulary Set",
  currentIndex: 6, // 0-indexed, displayed as 7 of 20
  totalCards: 20,
  masteredCount: 12,
  reviewCount: 3,
  recentlyLearned: [
    { term: "Execution", whenLabel: "2 mins ago" },
    { term: "Threshold", whenLabel: "15 mins ago" },
  ],
  needsReview: [{ term: "Infrastructure", whenLabel: "Yesterday" }],
};
