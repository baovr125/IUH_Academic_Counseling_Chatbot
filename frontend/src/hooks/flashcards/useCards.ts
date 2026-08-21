import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../useAuth";
import {
  fetchDeckCards,
  type BackendCardItem
} from "../../services/flashcardService";
import { getDecks as getLocalDecks } from "../../services/deckStorage";

export const getCardsQueryKey = (deckId?: string, userId?: string) => [
  "flashcard_cards",
  deckId,
  userId || "guest"
];

export function useCards(deckId?: string, deckLang: string = "en") {
  const { user } = useAuth();
  const userId = user?.id;

  const cardsQuery = useQuery({
    queryKey: getCardsQueryKey(deckId, userId),
    enabled: !!deckId,
    queryFn: async (): Promise<BackendCardItem[]> => {
      if (!deckId) return [];

      let cardsList: BackendCardItem[] = [];

      // Fetch from backend
      try {
        const res = await fetchDeckCards(deckId);
        if (res.ok && res.data) {
          cardsList = res.data.map((c) => ({
            ...c,
            lang_code: c.lang_code || c.langCode || deckLang,
            langCode: c.langCode || c.lang_code || deckLang
          }));
        }
      } catch (e) {
        console.warn("fetchDeckCards error in useCards:", e);
      }

      // Merge from local storage for offline / created local cards for this user
      const localDeck = getLocalDecks(userId).find((d) => d.id === deckId);
      if (localDeck && localDeck.cards && localDeck.cards.length > 0) {
        for (const lc of localDeck.cards) {
          if (!cardsList.some((c) => c.id === lc.id || c.term.toLowerCase() === lc.term.toLowerCase())) {
            cardsList.push({
              id: lc.id,
              deck_id: deckId,
              term: lc.term,
              definition: lc.definition,
              phonetic: lc.phonetic,
              audio_url: lc.audio_url,
              example_sentence: lc.example,
              example: lc.example,
              part_of_speech: lc.partOfSpeech || "phrase",
              lang_code: (lc as any).langCode || (lc as any).lang_code || deckLang,
              langCode: (lc as any).langCode || (lc as any).lang_code || deckLang,
              state: 0,
              stability: 0,
              difficulty: 0,
              due: new Date().toISOString(),
              recommended_mode: Math.random() < 0.3 ? "spelling" : "flip",
              cloze_sentence: lc.example ? lc.example.replace(new RegExp(lc.term, "gi"), "________") : undefined
            });
          }
        }
      }

      return cardsList;
    }
  });

  return {
    cards: cardsQuery.data || [],
    isLoadingCards: cardsQuery.isLoading,
    isErrorCards: cardsQuery.isError,
    refetchCards: cardsQuery.refetch
  };
}
