import { useState, useRef, useEffect } from "react";
import { Send, Square } from "lucide-react";
import { useSettings } from "../../context/SettingsContext";

interface ChatComposerProps {
  onSend: (content: string) => void;
  isSending: boolean;
  onAbort?: () => void;
}

export function ChatComposer({ onSend, isSending, onAbort }: ChatComposerProps) {
  let isVi = true;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const settings = useSettings();
    isVi = settings.language === "vi";
  } catch {
    // Fallback if rendered outside of SettingsProvider
  }

  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea vertically as content grows
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const maxHeight = 160; // Max vertical height ~ 6 lines
    const nextHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${Math.max(nextHeight, 24)}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [value]);

  const handleSend = () => {
    if (!value.trim() || isSending) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift), Shift+Enter creates a new line
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3 sm:px-6 dark:border-slate-700 dark:bg-slate-800/90">
      <div className="relative mx-auto max-w-4xl">
        <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 shadow-sm transition-all focus-within:border-orange-500 focus-within:ring-2 focus-within:ring-orange-500/20 dark:border-slate-700 dark:bg-slate-900/60 dark:focus-within:border-orange-500">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            maxLength={2000}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isVi
                ? "Hỏi Chatbot bất cứ thứ gì liên quan đến học tập..."
                : "Ask Chatbot anything about academic studies..."
            }
            className="flex-1 resize-none border-none bg-transparent py-1 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder:text-slate-500 leading-relaxed"
          />

          <div className="flex items-center gap-2 pb-0.5">
            <span className="text-[11px] text-slate-400 select-none hidden sm:inline">
              {value.length}/2000
            </span>

            {isSending ? (
              <button
                type="button"
                onClick={onAbort}
                className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-red-500 text-white shadow-md shadow-red-500/25 transition-all hover:bg-red-600 active:scale-95"
                title={isVi ? "Dừng phản hồi" : "Stop generating"}
              >
                <Square fill="currentColor" size={13} />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                disabled={!value.trim() || value.length > 2000}
                className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-orange-500 to-amber-500 text-white font-bold shadow-md shadow-orange-500/30 transition-all hover:from-orange-600 hover:to-amber-600 active:scale-95 disabled:cursor-not-allowed disabled:from-slate-200 disabled:to-slate-200 disabled:shadow-none dark:disabled:from-slate-700 dark:disabled:to-slate-700 disabled:opacity-60"
                title={isVi ? "Gửi câu hỏi" : "Send message"}
              >
                <Send size={15} />
              </button>
            )}
          </div>
        </div>

        <p className="mt-2 text-center text-[11px] text-slate-400 dark:text-slate-500 select-none">
          {isVi
            ? "Thông tin do AI tạo ra có thể cần kiểm chứng lại với các thông báo chính thức của nhà trường."
            : "AI-generated responses should be cross-checked with official university announcements."}
        </p>
      </div>
    </div>
  );
}
