import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../useAuth";
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
export const getDecksQueryKey = (userId?: string, langCode?: string) => ["flashcard_decks", userId || "guest", langCode || "all"];

/** Sổ thẻ của người dùng; có `langCode` thì chỉ lấy sổ của ngôn ngữ đó (lọc ở máy chủ) và đã xác nhận ngôn ngữ. */
export function useDecks(langCode?: string, enabled: boolean = true) {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  const decksQuery = useQuery({
    queryKey: getDecksQueryKey(userId, langCode),
    enabled,
    queryFn: async (): Promise<BackendDeck[]> => {
      let allDecks: BackendDeck[] = [];

      try {
        const res = await fetchBackendDecks(langCode);
        if (res.ok && res.data && res.data.length > 0) {
          allDecks = langCode ? res.data.filter((d) => d.lang_confirmed !== false) : [...res.data];
        }
      } catch (e) {
        console.warn("fetchBackendDecks error in useDecks:", e);
      }

      // Merge with local storage decks for this specific user
      const local = getLocalDecks(userId).filter((ld) => !langCode || ld.langCode === langCode);
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
      const res = await createBackendDeck(resolvedTitle, resolvedDesc, langCode);
      if (res.ok && res.data) {
        createdDeck = res.data;
      } else if (!res.ok && !res.error.network) {
        // Lỗi nghiệp vụ (vd 422 ngôn ngữ, 503 chưa migrate): báo cho người dùng, không tạo sổ giả cục bộ.
        throw new Error(res.error.message);
      }

      // Sync to local storage for this user (nếu không kết nối được máy chủ thì đây là bản lưu tạm duy nhất)
      const localDeck = createCustomDeck(langCode, resolvedTitle, resolvedDesc, createdDeck?.id, userId);
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
      queryClient.invalidateQueries({ queryKey: ["flashcard_language_summary"] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_language_cards"] });
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

      // Update local storage for this user
      const localDecks = getLocalDecks(userId);
      const target = localDecks.find((d) => d.id === id);
      if (target) {
        target.title = title.trim();
        target.description = description?.trim() || "";
        target.langCode = langCode;
        saveLocalDecks(localDecks, userId);
      }

      return { id, title: title.trim(), description: description?.trim() || "", lang_code: langCode };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["flashcard_language_summary"] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_language_cards"] });
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

      // Delete from local storage for this user
      const localDecks = getLocalDecks(userId).filter((d) => d.id !== deckId);
      saveLocalDecks(localDecks, userId);
      return deckId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DECKS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["flashcard_language_summary"] });
      queryClient.invalidateQueries({ queryKey: ["flashcard_language_cards"] });
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
