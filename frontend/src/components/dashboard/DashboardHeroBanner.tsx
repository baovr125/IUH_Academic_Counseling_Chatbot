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
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#152a6e] via-[#1e3a8a] to-[#2563eb] p-6 sm:p-8 text-white shadow-xl shadow-blue-950/15">
      {/* Decorative background glow circles */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-blue-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 right-1/3 h-48 w-48 rounded-full bg-orange-500/15 blur-2xl" />

      <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
        {/* Left info column */}
        <div className="space-y-3">
          {/* Tag / Badge */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur-md">
              {isStudent ? (
                <>
                  <GraduationCap size={14} className="text-orange-400" />
                  <span>Sinh viên IUH Chính quy</span>
                </>
              ) : (
                <>
                  <School size={14} className="text-emerald-300" />
                  <span>Thành viên Học thuật & Nghiên cứu</span>
                </>
              )}
            </span>

            {isStudent && stats.currentWeek && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-orange-500/80 px-2.5 py-0.5 text-xs font-medium text-white shadow-sm">
                <Calendar size={12} />
                <span>Tuần {stats.currentWeek} • {stats.semesterName || "HK1 2025-2026"}</span>
              </span>
            )}
          </div>

          {/* Heading */}
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Xin chào, {stats.userFullName} 👋
            </h1>
            <p className="mt-1 max-w-2xl text-sm sm:text-base text-blue-100/90 leading-relaxed font-normal">
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
            <div className="flex items-center gap-3 rounded-2xl bg-white/10 p-3.5 backdrop-blur-md border border-white/15">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500 text-white shadow-md shadow-orange-500/30">
                <Sparkles size={20} />
              </div>
              <div>
                <p className="text-xs text-blue-200">Trợ lý Học vụ AI</p>
                <p className="text-sm font-bold text-white">Sẵn sàng hỗ trợ 24/7</p>
              </div>
              <button
                type="button"
                onClick={() => navigate("/chat")}
                className="ml-2 flex h-8 w-8 items-center justify-center rounded-lg bg-white/20 text-white hover:bg-white hover:text-blue-900 transition-all cursor-pointer"
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
                className="group flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-orange-500/25 hover:from-orange-600 hover:to-amber-600 transition-all hover:scale-[1.02]"
              >
                <UserCheck size={16} />
                <span>Liên kết Mã Số Sinh Viên</span>
                <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
              </button>

              <button
                type="button"
                onClick={() => navigate("/translation-doc")}
                className="flex items-center justify-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 text-xs font-semibold text-white hover:bg-white/25 transition-all border border-white/20"
              >
                <BookOpen size={15} />
                <span>Dịch tài liệu PDF</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
