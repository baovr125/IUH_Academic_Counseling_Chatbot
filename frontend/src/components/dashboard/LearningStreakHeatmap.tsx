import React, { useState } from "react";
import { Flame, Calendar, Info } from "lucide-react";
import type { DashboardStats, LearningStreakDay } from "../../types";

interface LearningStreakHeatmapProps {
  stats: DashboardStats;
}

export const LearningStreakHeatmap: React.FC<LearningStreakHeatmapProps> = ({ stats }) => {
  const [hoveredDay, setHoveredDay] = useState<{ date: string; count: number } | null>(null);

  // 84 days = 12 weeks x 7 days
  const streakDays: LearningStreakDay[] = stats.streak && stats.streak.length === 84
    ? stats.streak
    : Array.from({ length: 84 }, (_, i) => ({
        date: new Date(Date.now() - (83 - i) * 86400000).toISOString().split("T")[0],
        intensity: ((i * 3 + 2) % 5) as 0 | 1 | 2 | 3 | 4,
        count: ((i * 3 + 2) % 5) * 2 + 1,
      }));

  const getIntensityClass = (intensity: number) => {
    switch (intensity) {
      case 4:
        return "bg-orange-500 hover:bg-orange-600";
      case 3:
        return "bg-orange-400 hover:bg-orange-500";
      case 2:
        return "bg-amber-300 hover:bg-amber-400";
      case 1:
        return "bg-orange-100 dark:bg-orange-950/70 hover:bg-orange-200";
      default:
        return "bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700";
    }
  };

  const daysOfWeek = ["T2", "T4", "T6", "CN"];

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700/60">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-100 text-orange-600 dark:bg-orange-950/60 dark:text-orange-400">
            <Flame size={16} className="fill-orange-500" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100">
              Chuỗi Hoạt Động Học Tập ({stats.streakDays} ngày)
            </h3>
            <p className="text-[10px] text-slate-400">Tần suất học tập & tương tác AI trong 12 tuần</p>
          </div>
        </div>

        <span className="text-[11px] font-bold text-orange-600 dark:text-orange-400">
          🔥 Đang duy trì
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="mt-4 overflow-x-auto pb-1">
        <div className="flex items-start gap-1.5 min-w-[280px]">
          {/* Day Labels */}
          <div className="flex flex-col justify-between text-[9px] font-medium text-slate-400 h-[88px] pr-1 py-0.5">
            <span>T2</span>
            <span>T4</span>
            <span>T6</span>
            <span>CN</span>
          </div>

          {/* 12 Columns of 7 Days */}
          <div className="grid grid-flow-col grid-rows-7 gap-1 flex-1">
            {streakDays.map((day, idx) => {
              const formattedDate = new Date(day.date).toLocaleDateString("vi-VN", {
                day: "2-digit",
                month: "2-digit",
              });
              const count = day.count ?? day.intensity * 3;

              return (
                <div
                  key={idx}
                  onMouseEnter={() => setHoveredDay({ date: formattedDate, count })}
                  onMouseLeave={() => setHoveredDay(null)}
                  className={`h-2.5 w-2.5 rounded-sm transition-all cursor-pointer ${getIntensityClass(
                    day.intensity
                  )}`}
                  title={`${formattedDate}: ${count} lượt hoạt động`}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer Info & Legend */}
      <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/60 text-[10px] text-slate-400">
        <div>
          {hoveredDay ? (
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {hoveredDay.date}: <span className="text-orange-600">{hoveredDay.count} hoạt động</span>
            </span>
          ) : (
            <span>Di chuột vào ô để xem chi tiết</span>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-1">
          <span>Ít</span>
          <div className="h-2 w-2 rounded-xs bg-slate-100 dark:bg-slate-800" />
          <div className="h-2 w-2 rounded-xs bg-orange-100 dark:bg-orange-950/70" />
          <div className="h-2 w-2 rounded-xs bg-amber-300" />
          <div className="h-2 w-2 rounded-xs bg-orange-400" />
          <div className="h-2 w-2 rounded-xs bg-orange-500" />
          <span>Nhiều</span>
        </div>
      </div>
    </div>
  );
};
