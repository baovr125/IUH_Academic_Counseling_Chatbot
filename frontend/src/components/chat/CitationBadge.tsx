import { BookMarked } from "lucide-react";
import type { Citation } from "../../types";

export function CitationBadge({ citation }: { citation: Citation }) {
  const content = (
    <span
      title={citation.snippet ?? citation.sourceTitle}
      className="inline-flex items-center gap-1 rounded-md bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 hover:bg-blue-200 transition-colors max-w-[200px]"
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
