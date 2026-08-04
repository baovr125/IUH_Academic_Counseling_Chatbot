import { useState, useRef } from "react";
import { FileText, SquarePen, Pencil, Trash2, AlertTriangle } from "lucide-react";
import type { ChatSession } from "../../types";

interface ChatHistoryPanelProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onRenameSession: (id: string, newTitle: string) => void;
  onDeleteSession: (id: string) => void;
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
  onRenameSession,
  onDeleteSession,
}: ChatHistoryPanelProps) {
  const { today, yesterday, older } = groupByRecency(sessions);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deletingTarget, setDeletingTarget] = useState<ChatSession | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const handleStartEdit = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleCommitEdit = (sessionId: string) => {
    if (editingId === sessionId) {
      if (editTitle.trim()) {
        onRenameSession(sessionId, editTitle.trim());
      }
      setEditingId(null);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setDeletingTarget(session);
  };

  const handleConfirmDelete = () => {
    if (deletingTarget) {
      onDeleteSession(deletingTarget.id);
      setDeletingTarget(null);
    }
  };

  const renderGroup = (label: string, items: ChatSession[]) =>
    items.length > 0 && (
      <div className="mb-3">
        <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          {label}
        </p>
        {items.map((session) => {
          const isEditing = editingId === session.id;
          const isActive = activeSessionId === session.id;

          if (isEditing) {
            return (
              <div key={session.id} className="px-1 py-1">
                <input
                  ref={inputRef}
                  type="text"
                  autoFocus
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => handleCommitEdit(session.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleCommitEdit(session.id);
                    } else if (e.key === "Escape") {
                      setEditingId(null);
                    }
                  }}
                  className="w-full rounded-md border border-blue-500 bg-white px-2 py-1 text-xs text-slate-800 focus:outline-none shadow-sm"
                />
              </div>
            );
          }

          return (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`group flex w-full cursor-pointer items-center justify-between gap-1.5 rounded-lg px-2 py-2 text-left text-sm transition-colors ${
                isActive
                  ? "bg-orange-50 text-orange-700 font-medium"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <FileText size={15} className="flex-shrink-0 text-slate-400" />
                <span className="truncate text-xs">{session.title}</span>
              </div>

              <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => handleStartEdit(e, session)}
                  title="Rename conversation"
                  className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
                >
                  <Pencil size={13} />
                </button>
                <button
                  onClick={(e) => handleDeleteClick(e, session)}
                  title="Delete conversation"
                  className="rounded p-1 text-slate-400 hover:bg-red-100 hover:text-red-600"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );

  return (
    <>
      <div className="flex h-full w-60 flex-shrink-0 flex-col border-r border-slate-200 bg-white px-2 py-3">
        <div className="mb-2 flex items-center justify-between px-2">
          <span className="text-sm font-semibold text-slate-700">Chat History</span>
          <button
            onClick={onNewChat}
            title="New chat"
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
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

      {/* --- Delete Confirmation Popup Modal --- */}
      {deletingTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-2xl border border-slate-100 animate-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
                <AlertTriangle size={20} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-800">Xác nhận xóa cuộc trò chuyện</h3>
                <p className="mt-1 text-xs text-slate-500">
                  Bạn có chắc chắn muốn xóa cuộc trò chuyện <strong className="text-slate-700">"{deletingTarget.title}"</strong> khỏi giao diện?
                </p>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                onClick={() => setDeletingTarget(null)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Hủy
              </button>
              <button
                onClick={handleConfirmDelete}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-700 shadow-sm transition-colors"
              >
                Xóa ngay
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
