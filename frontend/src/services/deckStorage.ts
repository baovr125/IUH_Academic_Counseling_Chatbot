import { getToken } from "./apiClient";
import type { Flashcard } from "../types";

/** Thẻ lưu cục bộ: `pendingSync` = lưu tạm khi máy chủ không kết nối được, chưa có trên backend. */
export type StoredCard = Flashcard & { pendingSync?: boolean };

export interface FlashcardDeck {
  id: string;
  langCode: string;
  title: string;
  description: string;
  iconFlag: string;
  cards: StoredCard[];
}

/**
 * 10 ngôn ngữ hệ thống. Khóa là MÃ NGÔN NGỮ ISO (en, de, zh, ja, ko, fr, es, ru, th, vi) — cùng mã với backend và
 * Realtime Translation. `flag` chỉ để hiển thị (cờ quốc gia GB/CN/JP/KR/VN không phải mã ngôn ngữ).
 * `learnable=false` (tiếng Việt) là ngôn ngữ giải nghĩa: chưa có bộ sưu tập để học.
 */
export interface LangMeta {
  label: string;
  flag: string;
  defaultTitle: string;
  /** Tên tiếng Việt, vd "Tiếng Đức". */
  viName: string;
  /** Tên bản ngữ, vd "Deutsch". */
  nativeName: string;
  learnable: boolean;
}

export const LANG_CONFIG: Record<string, LangMeta> = {
  en: { label: "Tiếng Anh (English)", flag: "🇬🇧", defaultTitle: "Sổ từ vựng Tiếng Anh", viName: "Tiếng Anh", nativeName: "English", learnable: true },
  de: { label: "Tiếng Đức (German)", flag: "🇩🇪", defaultTitle: "Sổ từ vựng Tiếng Đức", viName: "Tiếng Đức", nativeName: "Deutsch", learnable: true },
  zh: { label: "Tiếng Trung (Chinese)", flag: "🇨🇳", defaultTitle: "Sổ từ vựng Tiếng Trung", viName: "Tiếng Trung", nativeName: "中文", learnable: true },
  ja: { label: "Tiếng Nhật (Japanese)", flag: "🇯🇵", defaultTitle: "Sổ từ vựng Tiếng Nhật", viName: "Tiếng Nhật", nativeName: "日本語", learnable: true },
  ko: { label: "Tiếng Hàn (Korean)", flag: "🇰🇷", defaultTitle: "Sổ từ vựng Tiếng Hàn", viName: "Tiếng Hàn", nativeName: "한국어", learnable: true },
  fr: { label: "Tiếng Pháp (French)", flag: "🇫🇷", defaultTitle: "Sổ từ vựng Tiếng Pháp", viName: "Tiếng Pháp", nativeName: "Français", learnable: true },
  es: { label: "Tiếng Tây Ban Nha (Spanish)", flag: "🇪🇸", defaultTitle: "Sổ từ vựng Tiếng Tây Ban Nha", viName: "Tiếng Tây Ban Nha", nativeName: "Español", learnable: true },
  ru: { label: "Tiếng Nga (Russian)", flag: "🇷🇺", defaultTitle: "Sổ từ vựng Tiếng Nga", viName: "Tiếng Nga", nativeName: "Русский", learnable: true },
  th: { label: "Tiếng Thái (Thai)", flag: "🇹🇭", defaultTitle: "Sổ từ vựng Tiếng Thái", viName: "Tiếng Thái", nativeName: "ไทย", learnable: true },
  vi: { label: "Tiếng Việt (Vietnamese)", flag: "🇻🇳", defaultTitle: "Sổ từ vựng Tiếng Việt", viName: "Tiếng Việt", nativeName: "Tiếng Việt", learnable: false },
};

/** Thứ tự hiển thị chuẩn của 10 ngôn ngữ. */
export const LANG_CODES = Object.keys(LANG_CONFIG);
/** 9 ngôn ngữ có thể học (không gồm tiếng Việt). */
export const LEARNABLE_LANGS = LANG_CODES.filter((c) => LANG_CONFIG[c].learnable);

/** Chuẩn hóa "en-US" -> "en"; trả null nếu không thuộc 10 ngôn ngữ (không đoán, "auto" cũng là null). */
export function normalizeLangCode(code?: string | null): string | null {
  const base = (code || "").trim().toLowerCase().replace("_", "-").split("-")[0];
  return base in LANG_CONFIG ? base : null;
}

export function isLearnableLang(code?: string | null): boolean {
  const c = normalizeLangCode(code);
  return !!c && LANG_CONFIG[c].learnable;
}

function getStorageKey(userId?: string): string {
  if (userId && userId.trim() && userId !== "guest") {
    return `iuh_portal_ai_decks_${userId.trim()}`;
  }
  // Try extracting from sessionStorage token
  try {
    const token = getToken();
    if (token) {
      const parts = token.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        const uid = payload.sub || payload.id || payload.user_id;
        if (uid && String(uid).trim()) {
          return `iuh_portal_ai_decks_${String(uid).trim()}`;
        }
      }
    }
  } catch {
    // Ignore parse errors
  }
  return "iuh_portal_ai_decks_guest";
}

export function getDecks(userId?: string): FlashcardDeck[] {
  try {
    const key = getStorageKey(userId);
    const raw = localStorage.getItem(key);
    if (!raw) {
      return [];
    }
    const parsed: FlashcardDeck[] = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    return [];
  }
}

export function saveDecks(decks: FlashcardDeck[], userId?: string): void {
  try {
    const key = getStorageKey(userId);
    localStorage.setItem(key, JSON.stringify(decks));
  } catch (err) {
    console.error("Failed to save flashcard decks", err);
  }
}

export function addCardToDeck(
  targetLangCode: string,
  term: string,
  definition: string,
  example?: string,
  partOfSpeech?: string,
  deckId?: string,
  userId?: string,
  options: { pendingSync?: boolean } = {}
): { deck: FlashcardDeck; card: StoredCard } {
  const decks = getDecks(userId);
  const langMeta = LANG_CONFIG[targetLangCode] || {
    label: targetLangCode.toUpperCase(),
    flag: "🌐",
    defaultTitle: `Sổ từ vựng (${targetLangCode.toUpperCase()})`,
  };

  let deck: FlashcardDeck | undefined;
  if (deckId) {
    deck = decks.find((d) => d.id === deckId);
  }
  if (!deck && !deckId) {
    deck = decks.find((d) => d.langCode === targetLangCode);
  }
  if (!deck) {
    deck = {
      id: deckId || `deck_${targetLangCode}_${Date.now()}`,
      langCode: targetLangCode,
      title: langMeta.defaultTitle,
      description: `Sổ thẻ từ vựng được tạo tự động cho ${langMeta.label}`,
      iconFlag: langMeta.flag,
      cards: [],
    };
    decks.push(deck);
  }

  const newCard: StoredCard = {
    id: `fc_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    term: term.trim(),
    definition: definition.trim(),
    example: example || undefined,
    partOfSpeech: partOfSpeech || "phrase",
    ...(options.pendingSync ? { pendingSync: true } : {}),
  };

  // Avoid exact duplicate terms inside this deck
  const existsIndex = deck.cards.findIndex(
    (c) => c.term.toLowerCase() === newCard.term.toLowerCase()
  );
  if (existsIndex >= 0) {
    deck.cards[existsIndex] = { ...deck.cards[existsIndex], ...newCard };
  } else {
    deck.cards = [newCard, ...deck.cards];
  }
  saveDecks(decks, userId);

  return { deck, card: newCard };
}

export function createCustomDeck(
  langCode: string,
  title: string,
  description: string,
  customId?: string,
  userId?: string
): FlashcardDeck {
  const decks = getDecks(userId);
  const langMeta = LANG_CONFIG[langCode] || {
    label: langCode.toUpperCase(),
    flag: "🌐",
    defaultTitle: title,
  };

  const newDeck: FlashcardDeck = {
    id: customId || `deck_${langCode}_${Date.now()}`,
    langCode,
    title: title || langMeta.defaultTitle,
    description: description || `Sổ thẻ từ vựng ${langMeta.label}`,
    iconFlag: langMeta.flag,
    cards: [],
  };

  decks.push(newDeck);
  saveDecks(decks, userId);
  return newDeck;
}

export function deleteDeck(deckId: string, userId?: string): void {
  const decks = getDecks(userId).filter((d) => d.id !== deckId);
  saveDecks(decks, userId);
}
