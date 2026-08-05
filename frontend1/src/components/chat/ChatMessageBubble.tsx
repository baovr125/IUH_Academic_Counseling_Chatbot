import { useState } from "react";
import { Bot, ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";
import type { ChatMessage } from "../../types";
import { CitationBadge } from "./CitationBadge";
import { FormattedMarkdown } from "./FormattedMarkdown";
import { submitFeedback } from "../../services/chatService";

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
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState("");

  const handleFeedback = async (type: 'like' | 'dislike') => {
    // If clicking the same one, maybe toggle? Or just set it. We'll set it.
    const newFeedback = feedback === type ? null : type;
    setFeedback(newFeedback);
    if (newFeedback) {
      await submitFeedback(message.id, { feedback: newFeedback, comment });
    }
  };

  const handleCommentSubmit = async () => {
    if (!feedback && !comment) return;
    await submitFeedback(message.id, { feedback: feedback || 'like', comment });
    setShowComment(false);
  };

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
        {message.status === "pending" && !message.content ? (
          <TypingIndicator />
        ) : (
          <>
            <FormattedMarkdown content={message.content} />
            {message.status === "pending" && (
              <span className="inline-block h-3 w-1.5 animate-pulse rounded-sm bg-blue-400 ml-0.5 align-baseline" />
            )}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-blue-100 pt-2">
                <span className="text-xs text-slate-400">Nguồn:</span>
                {message.citations.map((c) => (
                  <CitationBadge key={c.id} citation={c} />
                ))}
              </div>
            )}
            {message.status === "complete" && (
              <div className="mt-3 flex flex-col gap-2 border-t border-blue-100 pt-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleFeedback('like')}
                    className={`p-1.5 rounded-md transition-colors ${feedback === 'like' ? 'bg-blue-100 text-blue-600' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'}`}
                    title="Hữu ích"
                  >
                    <ThumbsUp size={14} />
                  </button>
                  <button
                    onClick={() => handleFeedback('dislike')}
                    className={`p-1.5 rounded-md transition-colors ${feedback === 'dislike' ? 'bg-red-100 text-red-600' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'}`}
                    title="Không hữu ích"
                  >
                    <ThumbsDown size={14} />
                  </button>
                  <button
                    onClick={() => setShowComment(!showComment)}
                    className={`p-1.5 rounded-md transition-colors ${showComment ? 'bg-slate-200 text-slate-700' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'}`}
                    title="Thêm bình luận"
                  >
                    <MessageSquare size={14} />
                  </button>
                </div>
                {showComment && (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="text"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Nhập góp ý của bạn..."
                      className="flex-1 rounded-md border border-slate-200 px-3 py-1.5 text-xs text-slate-700 outline-none focus:border-blue-500"
                      onKeyDown={(e) => { if (e.key === 'Enter') handleCommentSubmit(); }}
                    />
                    <button
                      onClick={handleCommentSubmit}
                      className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                    >
                      Gửi
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
