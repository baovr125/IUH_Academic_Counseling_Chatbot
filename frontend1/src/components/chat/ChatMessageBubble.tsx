import { Bot } from "lucide-react";
import type { ChatMessage } from "../../types";
import { CitationBadge } from "./CitationBadge";
import { FormattedMarkdown } from "./FormattedMarkdown";

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400"
          style={{ animationDelay: `${i * 120}ms` }}
        />
      ))}
    </div>
  );
}

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[70%] rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-2.5 text-sm text-white">
          <FormattedMarkdown content={message.content} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2">
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-white">
        <Bot size={15} />
      </div>
      <div className="max-w-[75%] rounded-2xl rounded-tl-sm bg-blue-50 px-4 py-3 text-sm text-slate-700">
        {message.status === "pending" ? (
          <TypingIndicator />
        ) : (
          <>
            <FormattedMarkdown content={message.content} />
            {message.citations && message.citations.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-blue-100 pt-2">
                <span className="text-xs text-slate-400">Nguồn:</span>
                {message.citations.map((c) => (
                  <CitationBadge key={c.id} citation={c} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
