import { BookMarked } from "lucide-react";
import type { Citation } from "../../types";

export function CitationBadge({ citation }: { citation: Citation }) {
  return (
    <span
      title={citation.snippet ?? citation.sourceTitle}
      className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700"
    >
      <BookMarked size={11} />
      {citation.sourceTitle}
      {citation.pageOrSection ? `, ${citation.pageOrSection}` : ""}
    </span>
  );
}
