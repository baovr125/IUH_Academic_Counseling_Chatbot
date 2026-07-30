import { useDashboard } from "../hooks/useDashboard";
import { FileText } from "lucide-react";

export default function DashboardPage() {
  const { stats, isLoading } = useDashboard();

  if (isLoading || !stats) {
    return <div className="p-6 text-sm text-slate-400">Loading dashboard...</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 p-6 lg:grid-cols-3">
      <div className="rounded-xl bg-blue-700 p-5 text-white lg:col-span-2">
        <h2 className="text-lg font-semibold">Xin chào, {stats.userFullName}</h2>
        <p className="mt-1 text-sm text-blue-100">
          You have completed {stats.semesterCompletionPercent}% of your semester goals.
        </p>
        <div className="mt-3 text-3xl font-bold">{stats.semesterCompletionPercent}%</div>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <p className="text-xs text-slate-400">Vocabulary Learned</p>
        <p className="text-2xl font-bold text-slate-800">{stats.vocabularyLearnedToday} words</p>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <p className="text-xs text-slate-400">GPA Score</p>
        <p className="text-2xl font-bold text-slate-800">{stats.gpaScore}</p>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <p className="text-xs text-slate-400">Credits Earned</p>
        <p className="text-2xl font-bold text-slate-800">
          {stats.creditsEarned}/{stats.creditsTotal}
        </p>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <p className="text-xs text-slate-400">Learning Streaks</p>
        <p className="text-2xl font-bold text-orange-500">{stats.streakDays} days</p>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-sm lg:col-span-3">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Recent Documents</h3>
        <div className="space-y-2">
          {stats.recentDocuments.map((doc) => (
            <div key={doc.id} className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-slate-50">
              <FileText size={16} className="text-slate-400" />
              <span className="flex-1 text-sm text-slate-700">{doc.name}</span>
              <span className="text-xs text-slate-400">{doc.modifiedAt}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
