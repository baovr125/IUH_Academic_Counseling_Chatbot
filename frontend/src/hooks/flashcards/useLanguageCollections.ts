import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useAuth } from "../useAuth";
import {
  fetchLanguageCards,
  fetchLanguageSummary,
  type LanguageCardsPage,
  type LanguageCardsQuery,
  type LanguageSummary
} from "../../services/flashcardService";

export const LANGUAGE_SUMMARY_KEY = "flashcard_language_summary";
export const LANGUAGE_CARDS_KEY = "flashcard_language_cards";

/** Tổng hợp 10 bộ sưu tập ngôn ngữ. Luôn lấy lại khi vào màn hình để số liệu không lỗi thời. */
export function useLanguageSummary(options: { enabled?: boolean } = {}) {
  const { user } = useAuth();
  const query = useQuery({
    queryKey: [LANGUAGE_SUMMARY_KEY, user?.id || "guest"],
    enabled: options.enabled ?? true,
    staleTime: 0,
    queryFn: async (): Promise<LanguageSummary> => {
      const res = await fetchLanguageSummary();
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });
  return {
    summary: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    errorMessage: query.error instanceof Error ? query.error.message : null,
    refetch: query.refetch
  };
}

/** Từ vựng của một ngôn ngữ — tìm kiếm / lọc / sắp xếp / phân trang đều ở máy chủ. */
export function useLanguageCards(langCode: string | undefined, params: LanguageCardsQuery) {
  const { user } = useAuth();
  const query = useQuery({
    queryKey: [LANGUAGE_CARDS_KEY, langCode, user?.id || "guest", params],
    enabled: !!langCode,
    staleTime: 0,
    placeholderData: keepPreviousData,
    queryFn: async (): Promise<LanguageCardsPage> => {
      const res = await fetchLanguageCards(langCode as string, params);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });
  return {
    page: query.data,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    errorMessage: query.error instanceof Error ? query.error.message : null,
    refetch: query.refetch
  };
}
