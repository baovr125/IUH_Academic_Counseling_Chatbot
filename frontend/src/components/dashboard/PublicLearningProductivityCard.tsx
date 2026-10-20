import React from "react";
import { useNavigate } from "react-router-dom";
import {
  TrendingUp,
  FileCheck2,
  BookMarked,
  Clock,
  Flame,
  Plus,
  Sparkles,
} from "lucide-react";
import type { DashboardStats } from "../../types";
import { useFlashcardOverview } from "../../hooks/flashcards/useFlashcardOverview";
import { FcSkeleton } from "../flashcards/ui";
import { SampleDataBadge } from "./SampleDataBadge";

interface PublicLearningProductivityCardProps {
  stats: DashboardStats;
}

export const PublicLearningProductivityCard: React.FC<PublicLearningProductivityCardProps> = ({
  stats,
}) => {
  const navigate = useNavigate();
  const flashcards = useFlashcardOverview();
  const masteredLoading = flashcards.status === "loading";

  const totalDocs = stats.publicProductivity?.totalDocsTranslated ?? 18;
  const totalPages = stats.publicProductivity?.totalPagesProcessed ?? 142;
  const timeSaved = stats.publicProductivity?.timeSavedHours ?? 16.5;

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-700/60">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
            <TrendingUp size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Năng Suất Học Thuật Cá Nhân</h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Thống kê dịch thuật & từ vựng AI</p>
          </div>
        </div>

        <span className="flex items-center gap-1 rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-bold text-orange-700 dark:bg-orange-950/60 dark:text-orange-400">
          <Flame size={13} className="fill-orange-500" />
          {stats.streakSource === "live" ? `${stats.streakDays} ngày` : "—"}
        </span>
      </div>

      <div className="mt-5 space-y-4">
        {/* Metric Grid 2x2 */}
        <div className="grid grid-cols-2 gap-3">
          {/* Docs Translated */}
          <div className="rounded-2xl bg-blue-50/60 p-3.5 dark:bg-slate-900/60 border border-blue-100/50 dark:border-slate-700/50">
            <div className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400 text-xs font-semibold">
              <FileCheck2 size={15} />
              <span>Tài liệu đã dịch</span>
            </div>
            <SampleDataBadge className="mt-1.5" />
            <p className="mt-1.5 text-2xl font-extrabold text-slate-900 dark:text-white">
              {totalDocs}
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">{totalPages} trang PDF</p>
          </div>

          {/* Flashcards */}
          <div className="rounded-2xl bg-purple-50/60 p-3.5 dark:bg-slate-900/60 border border-purple-100/50 dark:border-slate-700/50">
            <div className="flex items-center gap-1.5 text-purple-600 dark:text-purple-400 text-xs font-semibold">
              <BookMarked size={15} />
              <span>Từ vựng đã học</span>
            </div>
            <div className="mt-1.5 text-2xl font-extrabold text-slate-900 dark:text-white" data-testid="mastered-value">
              {masteredLoading ? <FcSkeleton className="h-7 w-12" /> : flashcards.mastered === null ? "—" : flashcards.mastered.toLocaleString("vi-VN")}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Thẻ đã thuộc (FSRS)</p>
          </div>
        </div>

        {/* Time Saved Callout */}
        <div className="flex items-center justify-between rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 p-3.5 text-xs border border-emerald-100 dark:from-emerald-950/40 dark:to-teal-950/20 dark:border-emerald-900/40">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm">
              <Clock size={16} />
            </div>
            <div>
              <p className="text-slate-800 dark:text-slate-200 font-bold">Thời gian tiết kiệm nhờ AI</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Dịch nhanh & trích xuất ngữ cảnh</p>
              <SampleDataBadge className="mt-1" />
            </div>
          </div>
          <span className="text-base font-extrabold text-emerald-700 dark:text-emerald-400">
            ~{timeSaved}h
          </span>
        </div>

        {/* Quick Action Button */}
        <button
          type="button"
          onClick={() => navigate("/flashcards")}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer shadow-sm"
        >
          <Plus size={14} />
          <span>Tạo Bộ Thẻ Từ Vựng Mới</span>
        </button>
      </div>
    </div>
  );
};
