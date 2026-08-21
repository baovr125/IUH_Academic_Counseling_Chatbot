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
  role: "student",
  studentCode: "20045211",
  department: "Khoa Công nghệ Thông tin",
  major: "Kỹ thuật Phần mềm",
  semesterName: "Học kỳ 1 (2025 - 2026)",
  currentWeek: 12,
  semesterCompletionPercent: 78,
  lastSyncedAt: "Vừa cập nhật",
  vocabularyLearnedToday: 18,
  gpaScore: 3.82,
  gpaDelta: 0.14,
  creditsEarned: 112,
  creditsTotal: 145,
  streakDays: 28,
  streak: Array.from({ length: 84 }, (_, i) => ({
    date: new Date(Date.now() - (83 - i) * 86400000).toISOString(),
    intensity: [0, 1, 2, 3, 4][(i % 5) === 0 ? 0 : ((i * 3 + 2) % 5)] as 0 | 1 | 2 | 3 | 4,
    count: ((i * 3 + 2) % 5) * 3,
  })),
  recentDocuments: [
    {
      id: "d1",
      name: "Deep_Learning_Architectures_IEEE_2024.pdf",
      type: "pdf",
      modifiedAt: "10 phút trước",
      category: "research",
      pageCount: 14,
      fileSize: "2.4 MB",
      status: "completed",
      translatedTitle: "Kiến trúc Học sâu IEEE 2024 (Đã dịch sang Tiếng Việt)",
    },
    {
      id: "d2",
      name: "Quy_che_Dao_tao_Tin_chi_IUH_2024.pdf",
      type: "pdf",
      modifiedAt: "Hôm qua, 15:30",
      category: "handbook",
      pageCount: 38,
      fileSize: "4.8 MB",
      status: "completed",
      translatedTitle: "Quy chế Đào tạo Tín chỉ Đại học IUH 2024",
    },
    {
      id: "d3",
      name: "Software_Design_Patterns_GangOfFour.pdf",
      type: "pdf",
      modifiedAt: "2 ngày trước",
      category: "notes",
      pageCount: 22,
      fileSize: "3.1 MB",
      status: "completed",
      translatedTitle: "Mẫu Thiết kế Phần mềm (GoF - Slide Bài giảng)",
    },
  ],
  recentChatSessions: [
    {
      id: "s1",
      title: "Điều kiện xét Học bổng Khuyến khích Học tập HK2",
      lastMessage: "Theo quy định IUH, điểm GPA tối thiểu đạt loại Giỏi (từ 3.20 trở lên) và Điểm Rèn luyện >= 80...",
      updatedAt: "35 phút trước",
      messageCount: 4,
    },
    {
      id: "s2",
      title: "Thủ tục Hoãn thi & Phúc khảo Bài thi kết thúc học phần",
      lastMessage: "Đơn xin phúc khảo phải được nộp tại Văn phòng Một cửa trong vòng 07 ngày kể từ ngày công bố điểm...",
      updatedAt: "Hôm qua",
      messageCount: 6,
    },
    {
      id: "s3",
      title: "Chuẩn đầu ra Ngoại ngữ TOEIC / VSTEP cho ngành KTPM",
      lastMessage: "Sinh viên ngành Kỹ thuật Phần mềm cần đạt chứng chỉ TOEIC Quốc tế 500 điểm hoặc VSTEP B1...",
      updatedAt: "3 ngày trước",
      messageCount: 3,
    },
  ],
  flashcardSummary: {
    dueTodayCount: 16,
    totalMastered: 184,
    dailyGoal: 20,
    dailyLearned: 14,
    topDeckTitle: "Thuật ngữ Chuyên ngành CNTT (IT Terminology)",
    topDeckId: "deck_it_core",
    totalCards: 260,
  },
  academicDeadlines: [
    {
      id: "dl1",
      title: "Đăng ký Học phần Bổ sung Đợt 2 (Hệ Đại học Chính quy)",
      date: "25/08/2026 - 28/08/2026",
      daysRemaining: 4,
      type: "urgent",
      tag: "Cổng SV IUH",
      link: "https://sv.iuh.edu.vn",
    },
    {
      id: "dl2",
      title: "Hạn chót nộp Chứng chỉ Tiếng Anh xét Chuẩn đầu ra Đợt 3",
      date: "05/09/2026",
      daysRemaining: 15,
      type: "warning",
      tag: "Phòng Đào tạo",
    },
    {
      id: "dl3",
      title: "Hạn đóng Học phí Học kỳ 1 Năm học 2026 - 2027",
      date: "15/09/2026",
      daysRemaining: 25,
      type: "info",
      tag: "Phòng Tài chính",
    },
  ],
  publicProductivity: {
    totalDocsTranslated: 18,
    totalPagesProcessed: 142,
    totalWordsMastered: 248,
    timeSavedHours: 16.5,
  },
  admissionNews: [
    {
      id: "adm1",
      title: "Đề án Tuyển sinh Đại học Chính quy IUH 2026",
      date: "Mới cập nhật",
      badge: "Tuyển sinh",
      description: "Chỉ tiêu 9.500 sinh viên cho 60+ ngành đào tạo kỹ thuật, công nghệ và kinh tế.",
    },
    {
      id: "adm2",
      title: "Điểm chuẩn trúng tuyển theo phương thức ĐGNL & Học bạ",
      date: "Tuyển sinh 2026",
      badge: "Điểm chuẩn",
      description: "Ngành CNTT, Khoa học dữ liệu, Tự động hóa tiếp tục nằm trong nhóm ngành điểm cao nhất.",
    },
    {
      id: "adm3",
      title: "Chính sách Học bổng Thủ khoa & Tân sinh viên tài năng",
      date: "Học bổng",
      badge: "Học bổng 100%",
      description: "Trao học bổng toàn phần 100% học phí và hỗ trợ sinh hoạt phí cho thí sinh xuất sắc.",
    },
  ],
};

export function getMockDashboardStats(user?: User | null): DashboardStats {
  if (!user || user.role !== "student" || !user.studentCode) {
    // Non-student (Public / Guest / Researcher)
    return {
      ...MOCK_DASHBOARD_STATS,
      userFullName: user?.fullName || "Khách / Độc giả Học thuật",
      role: user?.role || "public",
      studentCode: undefined,
      department: user?.department || "Nghiên cứu & Học tập Tự do",
      major: user?.major || "Người dùng Ngoài IUH",
      gpaScore: 0,
      gpaDelta: 0,
      creditsEarned: 0,
      creditsTotal: 0,
      semesterCompletionPercent: 0,
      streakDays: 12,
      flashcardSummary: {
        dueTodayCount: 12,
        totalMastered: 142,
        dailyGoal: 15,
        dailyLearned: 9,
        topDeckTitle: "English for Academic Research & AI",
        topDeckId: "deck_research_ai",
        totalCards: 180,
      },
    };
  }

  // Student persona
  return {
    ...MOCK_DASHBOARD_STATS,
    userFullName: user.fullName || MOCK_DASHBOARD_STATS.userFullName,
    role: "student",
    studentCode: user.studentCode || "20045211",
    department: user.department || "Khoa Công nghệ Thông tin",
    major: user.major || "Kỹ thuật Phần mềm",
  };
}


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
const SAMPLE_PHRASES: Record<string, Record<string, string>> = {
  "tôi muốn đăng ký tín chỉ": {
    en: "I would like to register for academic credits.",
    de: "Ich möchte mich für Kreditpunkte anmelden.",
    zh: "我想选课登记 (学分)。",
    ja: "単位登録を申請したいです。",
    ko: "학점 수강 신청을 하고 싶습니다.",
    fr: "Je voudrais m'inscrire aux crédits universitaires.",
    es: "Me gustaría registrarme para los créditos académicos.",
    ru: "Я хотел бы зарегистрироваться на учебные кредиты.",
    th: "ฉันต้องการลงทะเบียนหน่วยกิต",
    vi: "Tôi muốn đăng ký tín chỉ.",
  },
  "chào bạn": {
    en: "Hello! How can I help you today?",
    de: "Hallo! Wie kann ich Ihnen helfen?",
    zh: "你好！今天有什么我可以帮你的？",
    ja: "こんにちは！どのようなご用件でしょうか？",
    ko: "안녕하세요! 무엇을 도와드릴까요?",
    fr: "Bonjour ! Comment puis-je vous aider ?",
    es: "¡Hola! ¿En qué puedo ayudarte?",
    ru: "Здравствуйте! Чем я могу помочь?",
    th: "สวัสดีครับ/ค่ะ มีอะไรให้ช่วยเหลือไหมครับ/คะ?",
    vi: "Chào bạn! Tôi có thể giúp gì cho bạn?",
  },
  "cảm ơn bạn": {
    en: "Thank you very much!",
    de: "Vielen Dank!",
    zh: "非常感谢你！",
    ja: "本当にありがとうございます！",
    ko: "정말 감사합니다!",
    fr: "Merci beaucoup !",
    es: "¡Muchas gracias!",
    ru: "Большое спасибо!",
    th: "ขอบคุณมากครับ/ค่ะ!",
    vi: "Cảm ơn bạn rất nhiều!",
  },
  "khoa công nghệ thông tin": {
    en: "Faculty of Information Technology (IUH)",
    de: "Fakultät für Informationstechnik",
    zh: "信息技术学院 (IUH)",
    ja: "情報技術学部 (IUH)",
    ko: "정보기술대학 (IUH)",
    fr: "Faculté des Technologies de l'Information",
    es: "Facultad de Tecnología de la Información",
    ru: "Факультет информационных технологий",
    th: "คณะเทคโนโลยีสารสนเทศ",
    vi: "Khoa Công nghệ Thông tin - Đại học Công nghiệp TP.HCM",
  },
};

const LANG_PREFIXES: Record<string, string> = {
  en: "[English]",
  de: "[German / Deutsch]",
  zh: "[Chinese / 中文]",
  ja: "[Japanese / 日本語]",
  ko: "[Korean / 한국어]",
  fr: "[French / Français]",
  es: "[Spanish / Español]",
  ru: "[Russian / Русский]",
  th: "[Thai / ไทย]",
  vi: "[Vietnamese / Tiếng Việt]",
};

export function mockTranslate(sourceText: string, targetLang: string): string {
  const key = sourceText.trim().toLowerCase();
  if (SAMPLE_PHRASES[key] && SAMPLE_PHRASES[key][targetLang]) {
    return SAMPLE_PHRASES[key][targetLang];
  }
  const prefix = LANG_PREFIXES[targetLang] || `[${targetLang.toUpperCase()}]`;
  return `${prefix} ${sourceText} (translated)`;
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
