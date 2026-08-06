import { Paperclip, Send, Square } from "lucide-react";
import { useState } from "react";

interface ChatComposerProps {
  onSend: (content: string) => void;
  isSending: boolean;
  onAbort?: () => void;
}

const QUICK_ACTIONS = [
  { label: "Tóm tắt quy chế", icon: "📄" },
  { label: "Tìm kiếm biểu mẫu", icon: "🔍" },
  { label: "Viết email xin phép", icon: "✉️" },
];

export function ChatComposer({ onSend, isSending, onAbort }: ChatComposerProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    if (!value.trim() || isSending) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="border-t border-slate-200 bg-white px-6 py-4">
      <div className="mb-3 flex flex-wrap gap-2">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            onClick={() => setValue(action.label)}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
          >
            <span className="mr-1">{action.icon}</span>
            {action.label}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
        <button className="text-slate-400 hover:text-slate-600" title="Attach file">
          <Paperclip size={18} />
        </button>
        <input
          value={value}
          maxLength={2000}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask the Knowledge Hub..."
          className="flex-1 border-none bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
        />
        <span className="text-xs text-slate-400 mr-2 select-none">
          {value.length}/2000
        </span>
        {isSending ? (
          <button
            onClick={onAbort}
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-red-100 text-red-600 transition-colors hover:bg-red-200"
            title="Stop generating"
          >
            <Square fill="currentColor" size={12} />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim() || value.length > 2000}
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-200"
          >
            <Send size={15} />
          </button>
        )}
      </div>

      <p className="mt-2 text-center text-[11px] text-slate-400">
        AI can make mistakes. Verify critical information.
      </p>
    </div>
  );
}
