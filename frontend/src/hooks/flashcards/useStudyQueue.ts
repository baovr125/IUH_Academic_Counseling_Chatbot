import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../useAuth";
import {
  fetchStudyQueue,
  fetchStudyStats,
  type BackendCardItem,
  type StudyStats
} from "../../services/flashcardService";

export const STUDY_QUERY_PREFIX = "flashcard_study";

/**
 * Hàng đợi học theo lịch FSRS của máy chủ (thẻ đến hạn trước, rồi thẻ mới) + thống kê tiến độ.
 *
 * - Hàng đợi chỉ tải một lần cho mỗi phiên (không tự làm mới khi đổi tab) để thứ tự thẻ không bị xáo giữa chừng.
 * - Deck chưa có trên máy chủ (chỉ ở LocalStorage) hoặc máy chủ lỗi: dùng `fallbackCards` làm hàng đợi.
 */
export function useStudyQueue(
  deckId: string | undefined,
  fallbackCards: BackendCardItem[],
  fallbackLoading: boolean
) {
  const { user } = useAuth();
  const userId = user?.id || "guest";
  const [weakQueue, setWeakQueue] = useState<BackendCardItem[] | null>(null);

  const statsQuery = useQuery({
    queryKey: [STUDY_QUERY_PREFIX, "stats", deckId, userId],
    enabled: !!deckId,
    staleTime: 0,
    queryFn: async (): Promise<StudyStats | null> => {
      const res = await fetchStudyStats(deckId as string);
      return res.ok ? res.data : null;
    }
  });

  const queueQuery = useQuery({
    queryKey: [STUDY_QUERY_PREFIX, "queue", deckId, userId],
    enabled: !!deckId,
    staleTime: Infinity,
    gcTime: 0,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    queryFn: async (): Promise<BackendCardItem[] | null> => {
      const res = await fetchStudyQueue(deckId as string);
      return res.ok ? res.data : null;
    }
  });

  const stats = statsQuery.data ?? null;
  const serverKnowsDeck = !!stats && stats.total > 0 && Array.isArray(queueQuery.data);
  const isFallback = !statsQuery.isLoading && !queueQuery.isLoading && !serverKnowsDeck;

  const refresh = useCallback(async () => {
    setWeakQueue(null);
    await Promise.all([statsQuery.refetch(), queueQuery.refetch()]);
  }, [statsQuery, queueQuery]);

  const refreshStats = useCallback(async () => {
    await statsQuery.refetch();
  }, [statsQuery]);

  /** Nạp danh sách các từ hay quên của deck để ôn riêng. Trả về số thẻ tìm thấy. */
  const loadWeak = useCallback(async (): Promise<number> => {
    if (!deckId) return 0;
    const res = await fetchStudyQueue(deckId, { weakOnly: true, newLimit: 0, limit: 100 });
    const cards = res.ok ? res.data : [];
    setWeakQueue(cards);
    return cards.length;
  }, [deckId]);

  const queue: BackendCardItem[] = weakQueue ?? (isFallback ? fallbackCards : queueQuery.data ?? []);
  const isLoading = statsQuery.isLoading || queueQuery.isLoading || (isFallback && fallbackLoading);

  return { queue, stats, isLoading, isFallback, refresh, refreshStats, loadWeak };
}
