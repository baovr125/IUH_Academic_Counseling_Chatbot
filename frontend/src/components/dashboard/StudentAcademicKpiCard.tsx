import React from "react";
import {
  Award,
  TrendingUp,
  GraduationCap,
  Flame,
  CheckCircle2,
  BookOpen,
} from "lucide-react";
import type { DashboardStats } from "../../types";

interface StudentAcademicKpiCardProps {
  stats: DashboardStats;
}

export const StudentAcademicKpiCard: React.FC<StudentAcademicKpiCardProps> = ({ stats }) => {
  const gpa = stats.gpaScore || 3.82;
  const delta = stats.gpaDelta || 0.14;
  const creditsEarned = stats.creditsEarned || 112;
  const creditsTotal = stats.creditsTotal || 145;
  const creditPercent = Math.min(100, Math.round((creditsEarned / (creditsTotal || 1)) * 100));
  const remainingCredits = Math.max(0, creditsTotal - creditsEarned);

  const getGpaClassification = (score: number) => {
    if (score >= 3.6) return { label: "Xuất sắc", color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-400" };
    if (score >= 3.2) return { label: "Giỏi", color: "text-blue-600 bg-blue-50 dark:bg-blue-950/60 dark:text-blue-400" };
    if (score >= 2.5) return { label: "Khá", color: "text-amber-600 bg-amber-50 dark:bg-amber-950/60 dark:text-amber-400" };
    return { label: "Trung bình", color: "text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-300" };
  };

  const gpaClass = getGpaClassification(gpa);

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-700/60">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
            <Award size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Tiến độ Học tập Cá nhân</h3>
            <p className="text-[11px] text-slate-400">Tích lũy tín chỉ & Điểm học phần</p>
          </div>
        </div>

        <span className="flex items-center gap-1 rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-bold text-orange-600 dark:bg-orange-950/60 dark:text-orange-400">
          <Flame size={13} className="fill-orange-500" />
          {stats.streakDays} ngày
        </span>
      </div>

      <div className="mt-5 space-y-5">
        {/* 1. GPA Score Big Number */}
        <div className="flex items-center justify-between rounded-2xl bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-slate-50 p-4 dark:from-slate-900/80 dark:to-slate-900/40 border border-blue-100/60 dark:border-slate-700/60">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Điểm GPA Tích lũy</p>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white">{gpa.toFixed(2)}</span>
              <span className="text-xs text-slate-400">/ 4.00</span>
            </div>
          </div>

          <div className="text-right space-y-1">
            <span className={`inline-block rounded-lg px-2.5 py-0.5 text-xs font-bold ${gpaClass.color}`}>
              {gpaClass.label}
            </span>
            <div className="flex items-center justify-end gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
              <TrendingUp size={12} />
              <span>+{delta.toFixed(2)} so với kỳ trước</span>
            </div>
          </div>
        </div>

        {/* 2. Credits Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-slate-600 dark:text-slate-300">Tín chỉ Tích lũy:</span>
            <span className="text-blue-600 dark:text-blue-400">
              {creditsEarned} / {creditsTotal} TC ({creditPercent}%)
            </span>
          </div>

          <div className="h-3 w-full rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-700"
              style={{ width: `${creditPercent}%` }}
            />
          </div>

          <div className="flex justify-between text-[11px] text-slate-400 pt-0.5">
            <span>Đã hoàn thành {creditsEarned} TC</span>
            <span>Còn lại {remainingCredits} TC tốt nghiệp</span>
          </div>
        </div>

        {/* 3. Semester Goal Progress */}
        <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 text-xs dark:bg-slate-900/60">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} className="text-emerald-500" />
            <span className="text-slate-600 dark:text-slate-300 font-medium">Mục tiêu kỳ này</span>
          </div>
          <span className="font-bold text-slate-800 dark:text-slate-200">{stats.semesterCompletionPercent}% Đạt</span>
        </div>
      </div>
    </div>
  );
};
