import { useCallback, useEffect, useState } from "react";
import { useAuth } from "./useAuth";

export const DAILY_GOAL_DEFAULT = 20;
export const DAILY_GOAL_MIN = 5;
export const DAILY_GOAL_MAX = 200;
/** Các mức gợi ý trên giao diện; người dùng vẫn có thể chọn mức bất kỳ trong khoảng cho phép. */
export const DAILY_GOAL_PRESETS = [10, 20, 30, 50] as const;

const storageKey = (userId?: string) => `iuh_flashcard_daily_goal_${userId && userId.trim() ? userId.trim() : "guest"}`;

/** Ép về số nguyên trong [MIN, MAX]; giá trị không hợp lệ thì dùng mặc định. */
export function clampDailyGoal(value: unknown): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return DAILY_GOAL_DEFAULT;
  return Math.min(DAILY_GOAL_MAX, Math.max(DAILY_GOAL_MIN, Math.round(n)));
}

function readGoal(userId?: string): number {
  try {
    const raw = window.localStorage.getItem(storageKey(userId));
    return raw === null ? DAILY_GOAL_DEFAULT : clampDailyGoal(raw);
  } catch {
    return DAILY_GOAL_DEFAULT; // localStorage bị chặn (chế độ riêng tư...) -> dùng mặc định
  }
}

/**
 * Mục tiêu số từ ôn mỗi ngày. Lưu trong localStorage theo từng tài khoản (không đồng bộ giữa thiết bị);
 * khi localStorage không dùng được thì mục tiêu vẫn đổi được trong phiên hiện tại.
 */
export function useDailyGoal() {
  const { user } = useAuth();
  const userId = user?.id;
  const [goal, setGoalState] = useState<number>(() => readGoal(userId));

  useEffect(() => {
    setGoalState(readGoal(userId));
  }, [userId]);

  const setGoal = useCallback(
    (next: number) => {
      const value = clampDailyGoal(next);
      setGoalState(value);
      try {
        window.localStorage.setItem(storageKey(userId), String(value));
      } catch {
        /* không lưu được thì chỉ giữ trong bộ nhớ */
      }
    },
    [userId]
  );

  return { goal, setGoal };
}
