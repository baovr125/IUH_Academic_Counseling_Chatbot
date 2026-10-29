import React from "react";
import { useNavigate } from "react-router-dom";
import {
  GraduationCap,
  Sparkles,
  UserCheck,
  ArrowRight,
  Calendar,
  BookOpen,
  School,
} from "lucide-react";
import type { DashboardStats, User } from "../../types";
import { isDocTranslationEnabled } from "../../config";

interface DashboardHeroBannerProps {
  user: User | null;
  stats: DashboardStats;
  isStudent: boolean;
}

export const DashboardHeroBanner: React.FC<DashboardHeroBannerProps> = ({
  stats,
  isStudent,
}) => {
  const navigate = useNavigate();

  return (
    <div className="relative overflow-hidden rounded-3xl border border-brand-100 bg-gradient-to-r from-brand-50 via-white to-sky-50 p-6 sm:p-8 text-slate-800 shadow-sm dark:border-slate-700 dark:from-slate-800 dark:via-slate-800 dark:to-brand-950/60 dark:text-white">
      {/* Decorative background glow circles */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-200/40 blur-3xl dark:bg-brand-400/20" />
      <div className="pointer-events-none absolute -bottom-16 right-1/3 h-48 w-48 rounded-full bg-sky-200/40 blur-2xl dark:bg-sky-500/10" />

      <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
        {/* Left info column */}
        <div className="space-y-3">
          {/* Tag / Badge */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-semibold text-brand-700 ring-1 ring-brand-100 dark:bg-white/10 dark:text-white dark:ring-0">
              {isStudent ? (
                <>
                  <GraduationCap size={14} className="text-brand-600 dark:text-brand-300" />
                  <span>Sinh viên IUH Chính quy</span>
                </>
              ) : (
                <>
                  <School size={14} className="text-emerald-600 dark:text-emerald-300" />
                  <span>Thành viên Học thuật & Nghiên cứu</span>
                </>
              )}
            </span>

            {isStudent && stats.currentWeek && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-600 px-2.5 py-0.5 text-xs font-medium text-white shadow-sm">
                <Calendar size={12} />
                <span>Tuần {stats.currentWeek} • {stats.semesterName || "HK1 2025-2026"}</span>
              </span>
            )}
          </div>

          {/* Heading */}
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-brand-900 dark:text-white">
              Xin chào, {stats.userFullName} 👋
            </h1>
            <p className="mt-1 max-w-2xl text-sm sm:text-base text-slate-600 dark:text-brand-100/90 leading-relaxed font-normal">
              {isStudent ? (
                <>
                  {stats.department ? `${stats.department} • ` : ""}
                  {stats.major ? `${stats.major} ` : ""}
                  {stats.studentCode ? `(MSSV: ${stats.studentCode})` : ""}
                </>
              ) : (
                "Chào mừng bạn đến với Cổng AI Dịch thuật, Nghiên cứu Tài liệu Học thuật & Khám phá Đại học Công nghiệp TP.HCM (IUH)."
              )}
            </p>
          </div>
        </div>

        {/* Right Action / Status Callout */}
        <div className="flex flex-shrink-0 flex-col sm:flex-row md:flex-col gap-2.5">
          {isStudent ? (
            <div className="flex items-center gap-3 rounded-2xl border border-brand-100 bg-white p-3.5 shadow-sm dark:border-white/15 dark:bg-white/10">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-md shadow-brand-600/25">
                <Sparkles size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-brand-200">Trợ lý Học vụ AI</p>
                <p className="text-sm font-bold text-slate-900 dark:text-white">Sẵn sàng hỗ trợ 24/7</p>
              </div>
              <button
                type="button"
                onClick={() => navigate("/chat")}
                className="ml-2 flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-600 hover:text-white dark:bg-white/20 dark:text-white dark:hover:bg-white dark:hover:text-brand-900 transition-all cursor-pointer"
                title="Hỏi Chatbot ngay"
              >
                <ArrowRight size={16} />
              </button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <button
                type="button"
                onClick={() => navigate("/profile")}
                className="group flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-brand-600/25 hover:bg-brand-700 transition-all hover:scale-[1.02]"
              >
                <UserCheck size={16} />
                <span>Liên kết Mã Số Sinh Viên</span>
                <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
              </button>

              {isDocTranslationEnabled() && (
                <button
                  type="button"
                  onClick={() => navigate("/translation-doc")}
                  className="flex items-center justify-center gap-2 rounded-xl border border-brand-200 bg-white px-4 py-2.5 text-xs font-semibold text-brand-700 hover:bg-brand-50 dark:border-white/20 dark:bg-white/15 dark:text-white dark:hover:bg-white/25 transition-all"
                >
                  <BookOpen size={15} />
                  <span>Dịch tài liệu PDF</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
