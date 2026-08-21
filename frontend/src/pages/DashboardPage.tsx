import React from "react";
import { useDashboard } from "../hooks/useDashboard";
import { useAuth } from "../hooks/useAuth";
import { DashboardHeroBanner } from "../components/dashboard/DashboardHeroBanner";
import { StudentDailyActionHub } from "../components/dashboard/StudentDailyActionHub";
import { PublicDocTranslationHub } from "../components/dashboard/PublicDocTranslationHub";
import { QuickTranslateWidget } from "../components/dashboard/QuickTranslateWidget";
import { RecentWorkspaceTabs } from "../components/dashboard/RecentWorkspaceTabs";
import { StudentAcademicKpiCard } from "../components/dashboard/StudentAcademicKpiCard";
import { PublicLearningProductivityCard } from "../components/dashboard/PublicLearningProductivityCard";
import { LearningStreakHeatmap } from "../components/dashboard/LearningStreakHeatmap";
import { IuhAcademicCalendarWidget } from "../components/dashboard/IuhAcademicCalendarWidget";
import { AdmissionAndEventsWidget } from "../components/dashboard/AdmissionAndEventsWidget";
import { Loader2 } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const { stats, isLoading, error } = useDashboard();

  // Role detection: verified student vs public / academic guest
  const isStudent = (user?.role === "student" && Boolean(user?.studentCode)) || (!user && true);

  if (isLoading || !stats) {
    return (
      <div className="flex min-h-full flex-col items-center justify-center p-12 bg-slate-50 dark:bg-slate-950">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-600/30 animate-bounce">
          <Loader2 size={28} className="animate-spin" />
        </div>
        <p className="mt-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
          Đang tải trung tâm điều khiển Dashboard...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <div className="mx-auto max-w-md rounded-2xl bg-red-50 p-6 text-red-700 dark:bg-red-950/50 dark:text-red-300">
          <p className="font-bold">Không thể tải dữ liệu Dashboard</p>
          <p className="mt-1 text-xs">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full w-full bg-slate-50/60 p-4 sm:p-6 lg:p-8 dark:bg-slate-950 transition-colors">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* 1. Header Hero Banner (Role-Adaptive) */}
        <DashboardHeroBanner user={user} stats={stats} isStudent={isStudent} />

        {/* 2. 12-Column Bento Grid Layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* LEFT 8 COLUMNS: INTERACTIVE WORKSPACE & ACTIONS */}
          <div className="space-y-6 lg:col-span-8">
            {/* Daily Action Hub (Student vs Public) */}
            {isStudent ? (
              <StudentDailyActionHub stats={stats} />
            ) : (
              <PublicDocTranslationHub stats={stats} />
            )}

            {/* Quick Translation Dock (Shared across all users) */}
            <QuickTranslateWidget />

            {/* Recent Workspace & Continuity Hub */}
            <RecentWorkspaceTabs stats={stats} isStudent={isStudent} />
          </div>

          {/* RIGHT 4 COLUMNS: ACADEMIC PROGRESS & CALENDAR / ADMISSION */}
          <div className="space-y-6 lg:col-span-4">
            {/* Academic KPI or Public Productivity */}
            {isStudent ? (
              <StudentAcademicKpiCard stats={stats} />
            ) : (
              <PublicLearningProductivityCard stats={stats} />
            )}

            {/* 12-Week Activity Streak Heatmap */}
            <LearningStreakHeatmap stats={stats} />

            {/* Academic Calendar or Admission Events */}
            {isStudent ? (
              <IuhAcademicCalendarWidget stats={stats} />
            ) : (
              <AdmissionAndEventsWidget stats={stats} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
