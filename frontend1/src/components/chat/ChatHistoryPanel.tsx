import { FileText, SquarePen } from "lucide-react";
import type { ChatSession } from "../../types";

interface ChatHistoryPanelProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
}

function groupByRecency(sessions: ChatSession[]) {
  const today: ChatSession[] = [];
  const yesterday: ChatSession[] = [];
  const older: ChatSession[] = [];

  const now = Date.now();
  for (const s of sessions) {
    const diffDays = Math.floor((now - new Date(s.updatedAt).getTime()) / 86400000);
    if (diffDays <= 0) today.push(s);
    else if (diffDays === 1) yesterday.push(s);
    else older.push(s);
  }
  return { today, yesterday, older };
}

export function ChatHistoryPanel({
  sessions,
  activeSessionId,
  isLoading,
  onSelectSession,
  onNewChat,
}: ChatHistoryPanelProps) {
  const { today, yesterday, older } = groupByRecency(sessions);

  const renderGroup = (label: string, items: ChatSession[]) =>
    items.length > 0 && (
      <div className="mb-3">
        <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          {label}
        </p>
        {items.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition-colors ${
              activeSessionId === session.id
                ? "bg-orange-50 text-orange-700"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <FileText size={15} className="flex-shrink-0 text-slate-400" />
            <span className="truncate">{session.title}</span>
          </button>
        ))}
      </div>
    );

  return (
    <div className="flex h-full w-56 flex-shrink-0 flex-col border-r border-slate-200 bg-white px-2 py-3">
      <div className="mb-2 flex items-center justify-between px-2">
        <span className="text-sm font-semibold text-slate-700">Chat History</span>
        <button onClick={onNewChat} title="New chat" className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
          <SquarePen size={15} />
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2 px-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-6 animate-pulse rounded bg-slate-100" />
          ))}
        </div>
      ) : (
        <div className="overflow-y-auto">
          {renderGroup("Today", today)}
          {renderGroup("Yesterday", yesterday)}
          {renderGroup("Older", older)}
        </div>
      )}
    </div>
  );
}
