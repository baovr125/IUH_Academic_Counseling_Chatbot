import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchBackendDecks,
  createBackendDeck,
  updateBackendDeck,
  deleteBackendDeck,
  type BackendDeck
} from "../../services/flashcardService";
import {
  getDecks as getLocalDecks,
  saveDecks as saveLocalDecks,
  createCustomDeck,
  LANG_CONFIG
} from "../../services/deckStorage";

export const DECKS_QUERY_KEY = ["flashcard_decks"];

export function useDecks() {
  const queryClient = useQueryClient();

  const decksQuery = useQuery({
    queryKey: DECKS_QUERY_KEY,
    queryFn: async (): Promise<BackendDeck[]> => {
      let allDecks: BackendDeck[] = [];

      try {
        const res = await fetchBackendDecks();
        if (res.ok && res.data && res.data.length > 0) {
          allDecks = [...res.data];
        }
      } catch (e) {
        console.warn("fetchBackendDecks error in useDecks:", e);
      }

      // Merge with local storage decks
      const local = getLocalDecks();
      for (const ld of local) {
        const existing = allDecks.find((d) => d.id === ld.id);
        if (!existing) {
          allDecks.push({
            id: ld.id,
            title: ld.title,
            description: ld.description,
            lang_code: ld.langCode,
            langCode: ld.langCode,
            icon_flag: ld.iconFlag,
            iconFlag: ld.iconFlag,
            cards_count: ld.cards ? ld.cards.length : 0
          });
        } else if (existing.cards_count === undefined || existing.cards_count === 0) {
          existing.cards_count = ld.cards ? ld.cards.length : 0;
        }
      }

      return allDecks;
    }
  });

  // Mutation: Create Deck
  const createDeckMutation = useMutation({
    mutationFn: async ({ title, description, langCode }: { title: string; description?: string; langCode: string }) => {
      const meta = LANG_CONFIG[langCode] || { flag: "🌐", defaultTitle: `Sổ từ vựng ${langCode.toUpperCase()}` };
      const resolvedTitle = title.trim() || meta.defaultTitle;
      const resolvedDesc = description?.trim() || `Sổ thẻ từ vựng ${meta.flag}`;

      let createdDeck: BackendDeck | null = null;
      try {
        const res = await createBackendDeck(resolvedTitle, resolvedDesc, langCode);
        if (res.ok && res.data) {
          createdDeck = res.data;
        }
      } catch (e) {
        console.warn("createBackendDeck error:", e);
      }

      // Sync to local storage
      const localDeck = createCustomDeck(langCode, resolvedTitle, resolvedDesc, createdDeck?.id);
      if (!createdDeck) {
        createdDeck = {
          id: localDeck.id,
          title: localDeck.title,
          description: localDeck.description,
          lang_code: localDeck.langCode,
          icon_flag: localDeck.iconFlag,
          cards_count: 0
        };
      }
      return createdDeck;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
    }
  });

  // Mutation: Update Deck
  const updateDeckMutation = useMutation({
    mutationFn: async ({ id, title, description, langCode }: { id: string; title: string; description?: string; langCode: string }) => {
      try {
        await updateBackendDeck(id, {
          title: title.trim(),
          description: description?.trim(),
          langCode
        });
      } catch (e) {
        console.warn("updateBackendDeck error:", e);
      }

      // Update local storage
      const localDecks = getLocalDecks();
      const target = localDecks.find((d) => d.id === id);
      if (target) {
        target.title = title.trim();
        target.description = description?.trim() || "";
        target.langCode = langCode;
        saveLocalDecks(localDecks);
      }

      return { id, title: title.trim(), description: description?.trim() || "", lang_code: langCode };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
    }
  });

  // Mutation: Delete Deck
  const deleteDeckMutation = useMutation({
    mutationFn: async (deckId: string) => {
      try {
        await deleteBackendDeck(deckId);
      } catch (e) {
        console.warn("deleteBackendDeck error:", e);
      }

      // Delete from local storage
      const localDecks = getLocalDecks().filter((d) => d.id !== deckId);
      saveLocalDecks(localDecks);
      return deckId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
    }
  });

  return {
    decks: decksQuery.data || [],
    isLoadingDecks: decksQuery.isLoading,
    isErrorDecks: decksQuery.isError,
    refetchDecks: decksQuery.refetch,
    createDeck: createDeckMutation.mutateAsync,
    isCreatingDeck: createDeckMutation.isPending,
    updateDeck: updateDeckMutation.mutateAsync,
    isUpdatingDeck: updateDeckMutation.isPending,
    deleteDeck: deleteDeckMutation.mutateAsync,
    isDeletingDeck: deleteDeckMutation.isPending
  };
}
