import { useState } from "react";
import { Bot, ThumbsUp, ThumbsDown, MessageSquare, Copy, Check } from "lucide-react";
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

export function ChatMessageBubble({ 
  message,
  isLatest = false,
  onSendMessage
}: { 
  message: ChatMessage;
  isLatest?: boolean;
  onSendMessage?: (msg: string) => void;
}) {
  const isUser = message.role === "user";
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState("");
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text', err);
    }
  };

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

  const followUpRegex = /\[follow_up\](.*?)\[\/follow_up\]/gs;
  const followUps: string[] = [];
  let match;
  while ((match = followUpRegex.exec(message.content)) !== null) {
    if (match[1].trim()) {
      followUps.push(match[1].trim());
    }
  }

  const cleanContent = message.content
    .replace(followUpRegex, '')
    .replace(/\[follow_up\][^\[]*$/, '')
    .trim();

  if (isUser) {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[70%] rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-2.5 text-sm text-white">
          <FormattedMarkdown content={cleanContent || message.content} />
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
            <FormattedMarkdown content={cleanContent} />
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
            {isLatest && followUps.length > 0 && (
              <div className="mt-3 flex flex-col gap-2">
                <span className="text-xs font-medium text-slate-500">Gợi ý câu hỏi:</span>
                <div className="flex flex-wrap gap-2">
                  {followUps.map((text, i) => (
                    <button
                      key={i}
                      onClick={() => onSendMessage && onSendMessage(text)}
                      className="text-left text-xs text-blue-700 bg-blue-100 hover:bg-blue-200 border border-blue-200 rounded-xl px-3 py-1.5 transition-colors"
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {message.status === "complete" && (
              <div className="mt-3 flex flex-col gap-2 border-t border-blue-100 pt-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopy}
                    className="p-1.5 rounded-md transition-colors text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                    title="Sao chép"
                  >
                    {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                  </button>
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
