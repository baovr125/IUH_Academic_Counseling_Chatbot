import type { Flashcard } from "../types";

export interface FlashcardDeck {
  id: string;
  langCode: string;
  title: string;
  description: string;
  iconFlag: string;
  cards: Flashcard[];
}

export const LANG_CONFIG: Record<
  string,
  { label: string; flag: string; defaultTitle: string }
> = {
  en: { label: "Tiếng Anh (English)", flag: "🇬🇧", defaultTitle: "Sổ từ vựng Tiếng Anh" },
  de: { label: "Tiếng Đức (German)", flag: "🇩🇪", defaultTitle: "Sổ từ vựng Tiếng Đức" },
  zh: { label: "Tiếng Trung (Chinese)", flag: "🇨🇳", defaultTitle: "Sổ từ vựng Tiếng Trung" },
  ja: { label: "Tiếng Nhật (Japanese)", flag: "🇯🇵", defaultTitle: "Sổ từ vựng Tiếng Nhật" },
  ko: { label: "Tiếng Hàn (Korean)", flag: "🇰🇷", defaultTitle: "Sổ từ vựng Tiếng Hàn" },
  fr: { label: "Tiếng Pháp (French)", flag: "🇫🇷", defaultTitle: "Sổ từ vựng Tiếng Pháp" },
  es: { label: "Tiếng Tây Ban Nha (Spanish)", flag: "🇪🇸", defaultTitle: "Sổ từ vựng Tiếng Tây Ban Nha" },
  ru: { label: "Tiếng Nga (Russian)", flag: "🇷🇺", defaultTitle: "Sổ từ vựng Tiếng Nga" },
  th: { label: "Tiếng Thái (Thai)", flag: "🇹🇭", defaultTitle: "Sổ từ vựng Tiếng Thái" },
  vi: { label: "Tiếng Việt (Vietnamese)", flag: "🇻🇳", defaultTitle: "Sổ từ vựng Tiếng Việt" },
};

const DECKS_STORAGE_KEY = "iuh_portal_ai_decks_v2";

const DEFAULT_DECKS: FlashcardDeck[] = [
  {
    id: "deck_en",
    langCode: "en",
    title: "Sổ từ vựng Tiếng Anh",
    description: "Từ vựng và mẫu câu học thuật Tiếng Anh",
    iconFlag: "🇬🇧",
    cards: [
      {
        id: "en_1",
        term: "Implementation",
        partOfSpeech: "noun",
        definition: "Sự triển khai, thực hiện một kế hoạch hoặc hệ thống.",
        example: "The implementation of artificial intelligence in modern portals.",
      },
      {
        id: "en_2",
        term: "Threshold",
        partOfSpeech: "noun",
        definition: "Ngưỡng, giới hạn bắt đầu của một trạng thái.",
        example: "The GPA score exceeded the scholarship threshold.",
      },
      {
        id: "en_3",
        term: "I would like to register for credits.",
        partOfSpeech: "phrase",
        definition: "Tôi muốn đăng ký tín chỉ.",
        example: "Dịch từ Tiếng Việt -> Tiếng Anh",
      },
    ],
  },
  {
    id: "deck_de",
    langCode: "de",
    title: "Sổ từ vựng Tiếng Đức",
    description: "Mẫu câu giao tiếp và học vụ Tiếng Đức",
    iconFlag: "🇩🇪",
    cards: [
      {
        id: "de_1",
        term: "Ich möchte mich für Kreditpunkte anmelden.",
        partOfSpeech: "phrase",
        definition: "Tôi muốn đăng ký tín chỉ.",
        example: "Dịch từ Tiếng Việt -> Tiếng Đức",
      },
      {
        id: "de_2",
        term: "Fakultät für Informationstechnik",
        partOfSpeech: "noun",
        definition: "Khoa Công nghệ Thông tin",
        example: "Dịch từ Tiếng Việt -> Tiếng Đức",
      },
      {
        id: "de_3",
        term: "Danke schön",
        partOfSpeech: "phrase",
        definition: "Cảm ơn bạn rất nhiều.",
        example: "Dịch từ Tiếng Việt -> Tiếng Đức",
      },
    ],
  },
  {
    id: "deck_ja",
    langCode: "ja",
    title: "Sổ từ vựng Tiếng Nhật",
    description: "Từ vựng và ngữ pháp Tiếng Nhật cơ bản",
    iconFlag: "🇯🇵",
    cards: [
      {
        id: "ja_1",
        term: "単位登録を申請したいです。",
        partOfSpeech: "phrase",
        definition: "Tôi muốn đăng ký tín chỉ.",
        example: "Dịch từ Tiếng Việt -> Tiếng Nhật",
      },
      {
        id: "ja_2",
        term: "情報技術学部",
        partOfSpeech: "noun",
        definition: "Khoa Công nghệ Thông tin",
        example: "Dịch từ Tiếng Việt -> Tiếng Nhật",
      },
    ],
  },
  {
    id: "deck_zh",
    langCode: "zh",
    title: "Sổ từ vựng Tiếng Trung",
    description: "Từ vựng Hán ngữ và hội thoại thường ngày",
    iconFlag: "🇨🇳",
    cards: [
      {
        id: "zh_1",
        term: "我想选课登记 (学分)。",
        partOfSpeech: "phrase",
        definition: "Tôi muốn đăng ký tín chỉ.",
        example: "Dịch từ Tiếng Việt -> Tiếng Trung",
      },
      {
        id: "zh_2",
        term: "信息技术学院",
        partOfSpeech: "noun",
        definition: "Khoa Công nghệ Thông tin",
        example: "Dịch từ Tiếng Việt -> Tiếng Trung",
      },
    ],
  },
  {
    id: "deck_ko",
    langCode: "ko",
    title: "Sổ từ vựng Tiếng Hàn",
    description: "Mẫu câu và thuật ngữ học đường Tiếng Hàn",
    iconFlag: "🇰🇷",
    cards: [
      {
        id: "ko_1",
        term: "학점 수강 신청을 하고 싶습니다.",
        partOfSpeech: "phrase",
        definition: "Tôi muốn đăng ký tín chỉ.",
        example: "Dịch từ Tiếng Việt -> Tiếng Hàn",
      },
    ],
  },
  {
    id: "deck_fr",
    langCode: "fr",
    title: "Sổ từ vựng Tiếng Pháp",
    description: "Từ vựng và diễn đạt Tiếng Pháp học vụ",
    iconFlag: "🇫🇷",
    cards: [
      {
        id: "fr_1",
        term: "Je voudrais m'inscrire aux crédits universitaires.",
        partOfSpeech: "phrase",
        definition: "Tôi muốn đăng ký tín chỉ.",
        example: "Dịch từ Tiếng Việt -> Tiếng Pháp",
      },
    ],
  },
];

export function getDecks(): FlashcardDeck[] {
  try {
    const raw = localStorage.getItem(DECKS_STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(DECKS_STORAGE_KEY, JSON.stringify(DEFAULT_DECKS));
      return DEFAULT_DECKS;
    }
    const parsed: FlashcardDeck[] = JSON.parse(raw);
    return parsed.length > 0 ? parsed : DEFAULT_DECKS;
  } catch (err) {
    return DEFAULT_DECKS;
  }
}

export function saveDecks(decks: FlashcardDeck[]): void {
  try {
    localStorage.setItem(DECKS_STORAGE_KEY, JSON.stringify(decks));
  } catch (err) {
    console.error("Failed to save flashcard decks", err);
  }
}

export function addCardToDeck(
  targetLangCode: string,
  term: string,
  definition: string,
  example?: string,
  partOfSpeech?: string
): { deck: FlashcardDeck; card: Flashcard } {
  const decks = getDecks();
  const langMeta = LANG_CONFIG[targetLangCode] || {
    label: targetLangCode.toUpperCase(),
    flag: "🌐",
    defaultTitle: `Sổ từ vựng (${targetLangCode.toUpperCase()})`,
  };

  let deck = decks.find((d) => d.langCode === targetLangCode);
  if (!deck) {
    deck = {
      id: `deck_${targetLangCode}_${Date.now()}`,
      langCode: targetLangCode,
      title: langMeta.defaultTitle,
      description: `Sổ thẻ từ vựng được tạo tự động cho ${langMeta.label}`,
      iconFlag: langMeta.flag,
      cards: [],
    };
    decks.push(deck);
  }

  const newCard: Flashcard = {
    id: `fc_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    term: term.trim(),
    definition: definition.trim(),
    example: example || `Dịch sang ${langMeta.label}`,
    partOfSpeech: partOfSpeech || "phrase",
  };

  // Avoid exact duplicate terms
  const exists = deck.cards.some(
    (c) => c.term.toLowerCase() === newCard.term.toLowerCase()
  );
  if (!exists) {
    deck.cards = [newCard, ...deck.cards];
    saveDecks(decks);
  }

  return { deck, card: newCard };
}

export function createCustomDeck(
  langCode: string,
  title: string,
  description: string
): FlashcardDeck {
  const decks = getDecks();
  const langMeta = LANG_CONFIG[langCode] || {
    label: langCode.toUpperCase(),
    flag: "🌐",
    defaultTitle: title,
  };

  const newDeck: FlashcardDeck = {
    id: `deck_${langCode}_${Date.now()}`,
    langCode,
    title: title || langMeta.defaultTitle,
    description: description || `Sổ thẻ từ vựng ${langMeta.label}`,
    iconFlag: langMeta.flag,
    cards: [],
  };

  decks.push(newDeck);
  saveDecks(decks);
  return newDeck;
}

export function deleteDeck(deckId: string): void {
  const decks = getDecks().filter((d) => d.id !== deckId);
  saveDecks(decks);
}
