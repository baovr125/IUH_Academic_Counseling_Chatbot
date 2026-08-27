import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../useAuth";
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
  const { user } = useAuth();
  const userId = user?.id;

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

      // Always sync to local storage for this user
      const localResult = addCardToDeck(
        langCode,
        term.trim(),
        definition.trim(),
        example?.trim() || undefined,
        partOfSpeech,
        targetDeckId,
        userId
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
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards", variables.deckId] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
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

      // Sync to local storage for this user
      const localDecks = getLocalDecks(userId);
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
          saveLocalDecks(localDecks, userId);
        }
      }

      return { cardId, term, definition, phonetic, example, partOfSpeech, langCode };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards", variables.deckId] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
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

      // Sync to local storage for this user
      const localDecks = getLocalDecks(userId);
      const targetDeck = localDecks.find((d) => d.id === targetDeckId);
      if (targetDeck && targetDeck.cards) {
        targetDeck.cards = targetDeck.cards.filter((c) => c.id !== cardId);
        saveLocalDecks(localDecks, userId);
      }

      return { cardId, deckId: targetDeckId };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards", variables.deckId] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
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
        queryClient.invalidateQueries({ queryKey: ["flashcard_cards", deckId] });
      }
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
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
      const cleanInput = userInput.trim();
      const cleanTerm = term.trim();
      const isLocalCard = !cardId || cardId.length < 10 || /^\d+$/.test(cardId);

      // Local Levenshtein distance calculation for offline/demo/local cards
      const evaluateLocally = (): VerifySpellingResult => {
        const s1 = cleanInput.toLowerCase();
        const s2 = cleanTerm.toLowerCase();
        const isMatch = s1 === s2;

        let similarity = isMatch ? 1.0 : 0.0;
        if (!isMatch && s1.length > 0 && s2.length > 0) {
          const matrix: number[][] = [];
          for (let i = 0; i <= s1.length; i++) matrix[i] = [i];
          for (let j = 0; j <= s2.length; j++) matrix[0][j] = j;
          for (let i = 1; i <= s1.length; i++) {
            for (let j = 1; j <= s2.length; j++) {
              if (s1[i - 1] === s2[j - 1]) matrix[i][j] = matrix[i - 1][j - 1];
              else matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
            }
          }
          const maxLen = Math.max(s1.length, s2.length);
          similarity = Math.max(0, 1 - matrix[s1.length][s2.length] / maxLen);
        }

        const isClose = !isMatch && similarity >= 0.75;
        let feedback = "";
        let suggestedGrade = 1;

        if (isMatch) {
          feedback = "Chính xác tuyệt đối! 🎉 Bạn đã ghi nhớ từ này rất xuất sắc.";
          suggestedGrade = 4; // Easy
        } else if (isClose) {
          feedback = `Gần đúng rồi! Lỗi chính tả nhỏ. Bạn gõ '${cleanInput}', đáp án đúng là '${cleanTerm}'.`;
          suggestedGrade = 2; // Hard
        } else {
          feedback = `Chưa chính xác. Đáp án đúng là '${cleanTerm}'. Hãy luyện tập thêm nhé!`;
          suggestedGrade = 1; // Again
        }

        return {
          is_correct: isMatch,
          is_close: isClose,
          similarity_score: similarity,
          correct_term: cleanTerm,
          user_input: cleanInput,
          feedback,
          suggested_grade: suggestedGrade,
          audio_url: fallbackAudio,
          phonetic: fallbackPhonetic,
          example_sentence: fallbackExample,
          lang_code: langCode
        };
      };

      // If local card or no backend token, grade locally (0ms, no 404 network errors)
      if (isLocalCard) {
        return evaluateLocally();
      }

      try {
        const res = await verifyCardSpelling(cardId, cleanInput, false);
        if (res.ok && res.data) {
          return res.data;
        }
      } catch {
        // Silent fallback
      }

      return evaluateLocally();
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

      // Sync imported cards to local storage fallback for this user
      if (res.data.cards && res.data.cards.length > 0) {
        const localDecks = getLocalDecks(userId);
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
          saveLocalDecks(localDecks, userId);
        }
      }

      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards", variables.deckId] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
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

