import type { ApiResult, DashboardStats, User } from "../types";
import { getMockDashboardStats } from "../mock/mockData";
import { fetchReviewStreak } from "./flashcardService";
import { delay } from "./utils";

/**
 * Thống kê dashboard. Phần chuỗi ngày học (heatmap 84 ngày, streak) lấy từ nhật ký ôn tập thật của người dùng
 * (`streakSource: "live"`); các chỉ số khác (GPA, tín chỉ...) vẫn là dữ liệu mẫu vì chưa có nguồn dữ liệu.
 * Số liệu Flashcard (đến hạn, đã thuộc, mục tiêu ngày) KHÔNG đi qua đây mà do `useFlashcardOverview` lấy trực tiếp
 * từ API Flashcard, để lỗi của một phần không chặn cả Dashboard.
 */
export async function fetchDashboardStats(user?: User | null): Promise<ApiResult<DashboardStats>> {
  const base = getMockDashboardStats(user);
  if (!user) {
    await delay(400);
    return { ok: true, data: base };
  }
  try {
    const res = await fetchReviewStreak(84);
    if (res.ok && res.data.days.length === 84) {
      return {
        ok: true,
        data: {
          ...base,
          streak: res.data.days,
          streakDays: res.data.current_streak,
          streakSource: "live"
        }
      };
    }
  } catch (error) {
    console.warn("fetchReviewStreak failed, using sample streak:", error);
  }
  return { ok: true, data: base };
}
