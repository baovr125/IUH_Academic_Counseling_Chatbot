import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../useAuth";
import { fetchReviewStreak, type ReviewStreakData } from "../../services/flashcardService";

export const REVIEW_STREAK_KEY = "flashcard_review_streak";

/**
 * Chuỗi ngày ôn tập (nguồn dữ liệu thật từ nhật ký ôn tập, cùng nguồn với Dashboard).
 * Chỉ là thông tin phụ: lỗi thì trả `undefined`, giao diện hiện dấu "—" chứ không chặn màn hình.
 * `staleTime: 0` (Dashboard) để số "đã ôn hôm nay" luôn mới sau khi vừa học xong.
 */
export function useReviewStreak(options: { enabled?: boolean; staleTime?: number } = {}) {
  const { user } = useAuth();
  const query = useQuery({
    queryKey: [REVIEW_STREAK_KEY, user?.id || "guest"],
    enabled: options.enabled ?? true,
    staleTime: options.staleTime ?? 60_000,
    retry: false,
    queryFn: async (): Promise<ReviewStreakData> => {
      const res = await fetchReviewStreak(7);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    }
  });
  return { streak: query.data, isLoading: query.isLoading, isError: query.isError, refetch: query.refetch };
}
