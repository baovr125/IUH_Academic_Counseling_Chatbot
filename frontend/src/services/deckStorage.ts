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

export function getDecks(): FlashcardDeck[] {
  try {
    const raw = localStorage.getItem(DECKS_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed: FlashcardDeck[] = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    return [];
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
  partOfSpeech?: string,
  deckId?: string
): { deck: FlashcardDeck; card: Flashcard } {
  const decks = getDecks();
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

  const newCard: Flashcard = {
    id: `fc_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    term: term.trim(),
    definition: definition.trim(),
    example: example || `Dịch sang ${langMeta.label}`,
    partOfSpeech: partOfSpeech || "phrase",
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
  saveDecks(decks);

  return { deck, card: newCard };
}

export function createCustomDeck(
  langCode: string,
  title: string,
  description: string,
  customId?: string
): FlashcardDeck {
  const decks = getDecks();
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
  saveDecks(decks);
  return newDeck;
}

export function deleteDeck(deckId: string): void {
  const decks = getDecks().filter((d) => d.id !== deckId);
  saveDecks(decks);
}
