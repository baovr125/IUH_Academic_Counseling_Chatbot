import React from "react";
import { Calendar, AlertCircle, Clock, ExternalLink, ChevronRight } from "lucide-react";
import type { DashboardStats, AcademicDeadline } from "../../types";

interface IuhAcademicCalendarWidgetProps {
  stats: DashboardStats;
}

export const IuhAcademicCalendarWidget: React.FC<IuhAcademicCalendarWidgetProps> = ({ stats }) => {
  const deadlines = stats.academicDeadlines || [];

  const getTypeStyles = (type: AcademicDeadline["type"]) => {
    switch (type) {
      case "urgent":
        return {
          dot: "bg-red-500 ring-red-100 dark:ring-red-950",
          badge: "bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-400",
        };
      case "warning":
        return {
          dot: "bg-amber-500 ring-amber-100 dark:ring-amber-950",
          badge: "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400",
        };
      default:
        return {
          dot: "bg-blue-500 ring-blue-100 dark:ring-blue-950",
          badge: "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400",
        };
    }
  };

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700/60">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
            <Calendar size={16} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100">
              Lịch Học Vụ & Sự Kiện IUH
            </h3>
            <p className="text-[10px] text-slate-400">Cổng thông tin đào tạo & khảo thí</p>
          </div>
        </div>

        <a
          href="https://sv.iuh.edu.vn"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400"
        >
          <span>Cổng SV</span>
          <ExternalLink size={11} />
        </a>
      </div>

      {/* Deadlines Timeline */}
      <div className="mt-4 space-y-3">
        {deadlines.map((dl) => {
          const styles = getTypeStyles(dl.type);
          return (
            <div
              key={dl.id}
              className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50/60 p-3 dark:border-slate-700/50 dark:bg-slate-900/40 hover:bg-slate-100/70 dark:hover:bg-slate-900/70 transition-colors"
            >
              <div className={`mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full ${styles.dot} ring-4`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1">
                  <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold ${styles.badge}`}>
                    {dl.tag}
                  </span>
                  {dl.daysRemaining !== undefined && (
                    <span className="text-[10px] font-semibold text-slate-400">
                      Còn {dl.daysRemaining} ngày
                    </span>
                  )}
                </div>
                <h4 className="mt-1 text-xs font-bold text-slate-800 dark:text-slate-200 leading-snug">
                  {dl.title}
                </h4>
                <div className="mt-1 flex items-center gap-1 text-[11px] text-slate-400">
                  <Clock size={11} />
                  <span>{dl.date}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
