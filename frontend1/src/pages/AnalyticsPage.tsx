import { useEffect, useState } from "react";
import { BarChart2, Activity, MessageSquare, ThumbsUp } from "lucide-react";

interface AnalyticsData {
  metrics: {
    avg_latency_ms: number;
    total_prompt_tokens: number;
    satisfaction_rate: number;
    total_feedback: number;
    like_count: number;
    dislike_count: number;
  };
  top_queries: { query: string; count: number }[];
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/analytics/overview")
      .then(res => res.json())
      .then(res => {
        if (res.ok) {
          setData(res.data);
        } else {
          setError(res.error?.message || "Failed to fetch analytics");
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-slate-500">Loading analytics...</div>;
  if (error) return <div className="p-8 text-red-500">Error: {error}</div>;
  if (!data) return <div className="p-8 text-slate-500">No data</div>;

  const maxQueryCount = data.top_queries.reduce((max, q) => Math.max(max, q.count), 1);

  return (
    <div className="flex-1 overflow-auto bg-slate-50 p-8 dark:bg-slate-900">
      <div className="mx-auto max-w-5xl space-y-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <BarChart2 className="text-blue-600" /> RAG Analytics Dashboard
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Latency */}
          <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 mb-2">
              <Activity size={20} />
              <span className="font-medium">Avg Latency</span>
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">
              {data.metrics.avg_latency_ms} <span className="text-lg font-normal text-slate-500">ms</span>
            </div>
          </div>

          {/* Prompt Tokens */}
          <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 mb-2">
              <MessageSquare size={20} />
              <span className="font-medium">Prompt Tokens</span>
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">
              {data.metrics.total_prompt_tokens.toLocaleString()}
            </div>
          </div>

          {/* Satisfaction */}
          <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 mb-2">
              <ThumbsUp size={20} />
              <span className="font-medium">Satisfaction</span>
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">
              {(data.metrics.satisfaction_rate * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {data.metrics.like_count} likes / {data.metrics.total_feedback} feedback
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Top 10 Most Common User Queries</h2>
          {data.top_queries.length === 0 ? (
            <p className="text-slate-500">No queries yet.</p>
          ) : (
            <div className="space-y-4">
              {data.top_queries.map((q, i) => (
                <div key={i} className="relative">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-slate-700 dark:text-slate-300">{q.query}</span>
                    <span className="text-slate-500 font-bold">{q.count}</span>
                  </div>
                  <div className="h-3 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full" 
                      style={{ width: `${(q.count / maxQueryCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
