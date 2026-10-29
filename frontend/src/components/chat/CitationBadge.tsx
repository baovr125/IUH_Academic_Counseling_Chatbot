import { BookMarked } from "lucide-react";
import type { Citation } from "../../types";

export function CitationBadge({ citation }: { citation: Citation }) {
  const content = (
    <span
      title={citation.snippet ?? citation.sourceTitle}
      className="inline-flex items-center gap-1 rounded-md bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700 hover:bg-brand-200 transition-colors max-w-[200px] dark:bg-brand-900/40 dark:text-brand-300 dark:hover:bg-brand-800/60"
    >
      <BookMarked size={11} className="flex-shrink-0" />
      <span className="truncate">
        {citation.sourceTitle}
        {citation.pageOrSection ? `, ${citation.pageOrSection}` : ""}
      </span>
    </span>
  );

  if (citation.url) {
    return (
      <a href={citation.url} target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    );
  }
  return content;
}
