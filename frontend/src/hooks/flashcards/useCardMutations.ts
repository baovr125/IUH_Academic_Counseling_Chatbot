import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createBackendCard,
  updateBackendCard,
  deleteBackendCard,
  submitFSRSReview,
  verifyCardSpelling,
  importDeckCardsFromExcel,
  type BackendCardItem,
  type VerifySpellingResult,
  type BulkImportResult
} from "../../services/flashcardService";
import {
  getDecks as getLocalDecks,
  saveDecks as saveLocalDecks,
  addCardToDeck
} from "../../services/deckStorage";
import { DECKS_QUERY_KEY } from "./useDecks";
import { getCardsQueryKey } from "./useCards";

export function useCardMutations(deckId?: string) {
  const queryClient = useQueryClient();

  // Mutation: Create Card
  const createCardMutation = useMutation({
    mutationFn: async ({
      deckId: targetDeckId,
      term,
      definition,
      phonetic,
      example,
      partOfSpeech,
      langCode
    }: {
      deckId: string;
      term: string;
      definition: string;
      phonetic?: string;
      example?: string;
      partOfSpeech: string;
      langCode: string;
    }): Promise<BackendCardItem> => {
      let createdCard: BackendCardItem | null = null;

      try {
        const res = await createBackendCard({
          deckId: targetDeckId,
          term: term.trim(),
          definition: definition.trim(),
          phonetic: phonetic?.trim() || undefined,
          exampleSentence: example?.trim() || undefined,
          partOfSpeech,
          langCode
        });

        if (res.ok && res.data) {
          createdCard = res.data;
        }
      } catch (e) {
        console.warn("createBackendCard error:", e);
      }

      // Always sync to local storage
      const localResult = addCardToDeck(
        langCode,
        term.trim(),
        definition.trim(),
        example?.trim() || undefined,
        partOfSpeech,
        targetDeckId
      );

      if (!createdCard) {
        createdCard = {
          id: localResult.card.id,
          deck_id: targetDeckId,
          term: term.trim(),
          definition: definition.trim(),
          phonetic: phonetic?.trim() || undefined,
          example_sentence: example?.trim() || undefined,
          part_of_speech: partOfSpeech,
          lang_code: langCode,
          state: 0,
          due: new Date().toISOString(),
          recommended_mode: "flip"
        };
      }

      return createdCard;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: getCardsQueryKey(variables.deckId) });
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
    }
  });

  // Mutation: Update Card
  const updateCardMutation = useMutation({
    mutationFn: async ({
      cardId,
      deckId: targetDeckId,
      term,
      definition,
      phonetic,
      example,
      partOfSpeech,
      langCode
    }: {
      cardId: string;
      deckId: string;
      term: string;
      definition: string;
      phonetic?: string;
      example?: string;
      partOfSpeech: string;
      langCode: string;
    }) => {
      try {
        await updateBackendCard(cardId, {
          term: term.trim(),
          definition: definition.trim(),
          phonetic: phonetic?.trim() || undefined,
          exampleSentence: example?.trim() || undefined,
          partOfSpeech,
          langCode
        });
      } catch (e) {
        console.warn("updateBackendCard error:", e);
      }

      // Sync to local storage
      const localDecks = getLocalDecks();
      const targetDeck = localDecks.find((d) => d.id === targetDeckId);
      if (targetDeck && targetDeck.cards) {
        const cIdx = targetDeck.cards.findIndex((c) => c.id === cardId);
        if (cIdx >= 0) {
          targetDeck.cards[cIdx] = {
            ...targetDeck.cards[cIdx],
            term: term.trim(),
            definition: definition.trim(),
            phonetic: phonetic?.trim() || undefined,
            example: example?.trim() || undefined,
            partOfSpeech
          };
          saveLocalDecks(localDecks);
        }
      }

      return { cardId, term, definition, phonetic, example, partOfSpeech, langCode };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: getCardsQueryKey(variables.deckId) });
    }
  });

  // Mutation: Delete Card
  const deleteCardMutation = useMutation({
    mutationFn: async ({ cardId, deckId: targetDeckId }: { cardId: string; deckId: string }) => {
      try {
        await deleteBackendCard(cardId);
      } catch (e) {
        console.warn("deleteBackendCard error:", e);
      }

      // Sync to local storage
      const localDecks = getLocalDecks();
      const targetDeck = localDecks.find((d) => d.id === targetDeckId);
      if (targetDeck && targetDeck.cards) {
        targetDeck.cards = targetDeck.cards.filter((c) => c.id !== cardId);
        saveLocalDecks(localDecks);
      }

      return { cardId, deckId: targetDeckId };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: getCardsQueryKey(variables.deckId) });
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
    }
  });

  // Rate FSRS
  const rateFSRSMutation = useMutation({
    mutationFn: async ({ cardId, grade }: { cardId: string; grade: number }) => {
      return await submitFSRSReview(cardId, grade);
    },
    onSuccess: () => {
      if (deckId) {
        queryClient.invalidateQueries({ queryKey: getCardsQueryKey(deckId) });
      }
    }
  });

  // Verify Spelling
  const verifySpellingMutation = useMutation({
    mutationFn: async ({ cardId, userInput, term, fallbackPhonetic, fallbackExample, fallbackAudio, langCode }: {
      cardId: string;
      userInput: string;
      term: string;
      fallbackPhonetic?: string;
      fallbackExample?: string;
      fallbackAudio?: string;
      langCode?: string;
    }): Promise<VerifySpellingResult> => {
      const res = await verifyCardSpelling(cardId, userInput.trim(), false);
      if (res.ok && res.data) {
        return res.data;
      }
      // Fallback local verify
      const isMatch = userInput.trim().toLowerCase() === term.trim().toLowerCase();
      return {
        is_correct: isMatch,
        is_close: false,
        similarity_score: isMatch ? 1.0 : 0.0,
        correct_term: term,
        user_input: userInput,
        feedback: isMatch ? "Chính xác tuyệt đối! 🎉" : `Chưa đúng. Đáp án: ${term}`,
        suggested_grade: isMatch ? 4 : 1,
        audio_url: fallbackAudio,
        phonetic: fallbackPhonetic,
        example_sentence: fallbackExample,
        lang_code: langCode
      };
    }
  });

  // Mutation: Bulk Import Excel / CSV
  const importExcelMutation = useMutation({
    mutationFn: async ({ deckId: targetDeckId, file, langCode }: { deckId: string; file: File; langCode?: string }): Promise<BulkImportResult> => {
      const res = await importDeckCardsFromExcel(targetDeckId, file, langCode);
      if (!res.ok) {
        throw new Error(res.error?.message || "Lỗi nhập file Excel");
      }
      if (!res.data) {
        throw new Error("Không nhận được dữ liệu phản hồi từ máy chủ");
      }

      // Sync imported cards to local storage fallback
      if (res.data.cards && res.data.cards.length > 0) {
        const localDecks = getLocalDecks();
        const targetDeck = localDecks.find((d) => d.id === targetDeckId);
        if (targetDeck) {
          if (!targetDeck.cards) targetDeck.cards = [];
          for (const c of res.data.cards) {
            if (!targetDeck.cards.some((tc) => tc.id === c.id || tc.term.toLowerCase() === c.term.toLowerCase())) {
              targetDeck.cards.push({
                id: c.id,
                term: c.term,
                definition: c.definition,
                phonetic: c.phonetic,
                audio_url: c.audio_url,
                example: c.example_sentence || c.example,
                partOfSpeech: c.part_of_speech
              });
            }
          }
          saveLocalDecks(localDecks);
        }
      }

      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: getCardsQueryKey(variables.deckId) });
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
    }
  });

  return {
    createCard: createCardMutation.mutateAsync,
    isCreatingCard: createCardMutation.isPending,
    updateCard: updateCardMutation.mutateAsync,
    isUpdatingCard: updateCardMutation.isPending,
    deleteCard: deleteCardMutation.mutateAsync,
    isDeletingCard: deleteCardMutation.isPending,
    rateFSRS: rateFSRSMutation.mutateAsync,
    isRatingFSRS: rateFSRSMutation.isPending,
    verifySpelling: verifySpellingMutation.mutateAsync,
    isVerifyingSpelling: verifySpellingMutation.isPending,
    importExcel: importExcelMutation.mutateAsync,
    isImportingExcel: importExcelMutation.isPending
  };
}

