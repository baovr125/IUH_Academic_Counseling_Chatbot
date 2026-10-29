import { useState } from "react";
import { Bot, RefreshCw, ThumbsUp, ThumbsDown, MessageSquare, Copy, Check } from "lucide-react";
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
  onSendMessage,
  previousUserMessage
}: { 
  message: ChatMessage;
  isLatest?: boolean;
  onSendMessage?: (
    msg: string, 
    bypassCache?: boolean, 
    replaceMessageIds?: { userMsgId?: string; assistantMsgId?: string }
  ) => void;
  previousUserMessage?: ChatMessage;
}) {
  const isUser = message.role === "user";
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState("");
  const [copied, setCopied] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

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

  const followUpRegex = /<query>(.*?)<\/query>/gs;
  const followUps: string[] = [];
  let match;
  
  // Extract queries ONLY from the final part of the message (after the thought block)
  // This prevents capturing suggested queries that the model drafted inside <think>
  const contentAfterThought = message.content.replace(/<think>[\s\S]*?<\/think>\n*/gi, '');
  while ((match = followUpRegex.exec(contentAfterThought)) !== null) {
    if (match[1].trim()) {
      followUps.push(match[1].trim());
    }
  }

  // Hide the thought block from the final UI, but if it's currently streaming the thought,
  // show a "Thinking..." indicator
  const isThinking = /<think>(?![\s\S]*<\/think>)/i.test(message.content);
  
  let cleanContent = message.content
    .replace(/<think>[\s\S]*?<\/think>\n*/gi, '') // Strip out completed Chain-of-Thought thinking tags
    .replace(/<think>[\s\S]*$/i, isThinking ? '_Đang suy nghĩ..._' : '') // Show indicator while streaming
    .replace(/<suggested_queries>[\s\S]*?<\/suggested_queries>\n*/gi, '') // Strip out entire suggested queries block
    .replace(/<suggested_queries>[\s\S]*$/i, '') // Strip out incomplete suggested queries block while streaming
    .replace(/\n*\*?Nguồn:\*?[\s\S]*$/i, '') // Strip out Nguồn: block if AI hallucinates it
    .replace(/\n*\*?Tham khảo:\*?[\s\S]*$/i, '') // Strip out Tham khảo: block
    .trim();

  const uniqueCitations = (message.citations || []).reduce((acc, current) => {
    // Aggressively deduplicate by sourceTitle ONLY, ignoring different URLs 
    // to ensure they collapse into exactly 1 badge.
    const key = current.sourceTitle;
    if (!acc.find(item => item.sourceTitle === key)) {
      acc.push(current);
    }
    return acc;
  }, [] as NonNullable<typeof message.citations>);

  if (isUser) {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[88%] sm:max-w-[70%] break-words rounded-2xl rounded-tr-sm bg-brand-600 px-4 py-2.5 text-sm text-white">
          <FormattedMarkdown content={cleanContent || message.content} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2">
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-brand-600 text-white">
        <Bot size={15} />
      </div>
      <div className="min-w-0 max-w-[calc(100%-2.25rem)] sm:max-w-[75%] rounded-2xl rounded-tl-sm bg-brand-50 px-4 py-3 text-sm text-slate-700 dark:bg-brand-950/40 dark:text-slate-200">
        {message.status === "pending" && !message.content ? (
          <TypingIndicator />
        ) : (
          <>
            <FormattedMarkdown content={cleanContent} />
            {message.status === "pending" && (
              <span className="inline-block h-3 w-1.5 animate-pulse rounded-sm bg-brand-400 ml-0.5 align-baseline" />
            )}
            {uniqueCitations && uniqueCitations.length > 0 && (
              <div className="mt-2 flex flex-col gap-1.5 border-t border-brand-100 pt-2 dark:border-brand-900/50">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs text-slate-400">Nguồn:</span>
                  {(sourcesExpanded ? uniqueCitations : uniqueCitations.slice(0, 2)).map((c) => (
                    <CitationBadge key={c.id} citation={c} />
                  ))}
                  {!sourcesExpanded && uniqueCitations.length > 2 && (
                    <button
                      onClick={() => setSourcesExpanded(true)}
                      className="text-xs text-brand-500 hover:text-brand-700 underline px-1 [@media(pointer:coarse)]:py-3 dark:text-brand-400 dark:hover:text-brand-300"
                    >
                      +{uniqueCitations.length - 2} xem thêm
                    </button>
                  )}
                  {sourcesExpanded && uniqueCitations.length > 2 && (
                    <button
                      onClick={() => setSourcesExpanded(false)}
                      className="text-xs text-slate-400 hover:text-slate-600 underline px-1 [@media(pointer:coarse)]:py-3 dark:hover:text-slate-200"
                    >
                      Thu gọn
                    </button>
                  )}
                </div>
              </div>
            )}
            {isLatest && followUps.length > 0 && (
              <div className="mt-3 flex flex-col gap-2">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Gợi ý câu hỏi tiếp theo:</span>
                <div className="flex flex-wrap gap-2">
                  {followUps.map((text, i) => (
                    <button
                      key={i}
                      onClick={() => onSendMessage && onSendMessage(text)}
                      className="text-left text-xs font-semibold text-brand-800 bg-brand-50 hover:bg-brand-100 border border-brand-200/90 rounded-xl px-3 py-1.5 [@media(pointer:coarse)]:py-2.5 transition-all shadow-xs hover:border-brand-300 active:scale-95 dark:text-brand-200 dark:bg-brand-950/50 dark:border-brand-800/60 dark:hover:bg-brand-900/60"
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {message.status === "complete" && (
              <div className="mt-3 flex flex-col gap-2 border-t border-slate-100 pt-2 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopy}
                    className="p-1.5 [@media(pointer:coarse)]:p-3 rounded-md transition-colors text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-200"
                    title="Sao chép"
                  >
                    {copied ? <Check size={14} className="text-green-500 dark:text-green-400" /> : <Copy size={14} />}
                  </button>
                  <button
                    onClick={() => handleFeedback('like')}
                    className={`p-1.5 [@media(pointer:coarse)]:p-3 rounded-md transition-colors ${feedback === 'like' ? 'bg-brand-100 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-200'}`}
                    title="Hữu ích"
                  >
                    <ThumbsUp size={14} />
                  </button>
                  <button
                    onClick={() => handleFeedback('dislike')}
                    className={`p-1.5 [@media(pointer:coarse)]:p-3 rounded-md transition-colors ${feedback === 'dislike' ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-300' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-200'}`}
                    title="Không hữu ích"
                  >
                    <ThumbsDown size={14} />
                  </button>
                  <button
                    onClick={() => setShowComment(!showComment)}
                    className={`p-1.5 [@media(pointer:coarse)]:p-3 rounded-md transition-colors ${showComment ? 'bg-brand-100 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-200'}`}
                    title="Thêm bình luận"
                  >
                    <MessageSquare size={14} />
                  </button>
                  {message.cacheStatus === "HIT" && previousUserMessage && onSendMessage && (
                    <button
                      onClick={() =>
                        onSendMessage(previousUserMessage.content, true, {
                          userMsgId: previousUserMessage.id,
                          assistantMsgId: message.id,
                        })
                      }
                      className="flex items-center gap-1 p-1.5 rounded-lg transition-colors text-brand-600 hover:bg-brand-50 ml-auto text-xs font-bold dark:text-brand-400 dark:hover:bg-brand-950/50"
                      title="Bỏ qua cache và tạo lại câu trả lời mới"
                    >
                      <RefreshCw size={12} />
                      Tạo lại
                    </button>
                  )}
                </div>
                {showComment && (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="text"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Nhập góp ý của bạn..."
                      className="flex-1 rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-700 outline-none focus:border-brand-500 dark:border-slate-600 dark:text-slate-200"
                      onKeyDown={(e) => { if (e.key === 'Enter') handleCommentSubmit(); }}
                    />
                    <button
                      onClick={handleCommentSubmit}
                      className="rounded-xl bg-brand-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-brand-700 transition-all active:scale-95"
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
