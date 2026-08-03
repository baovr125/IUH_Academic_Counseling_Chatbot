import React from "react";

interface FormattedMarkdownProps {
  content: string;
}

function parseInline(text: string): React.ReactNode[] {
  // Matches **bold**, __bold__, *italic*, _italic_, and [link](url)
  const regex = /(\*\*[^*]+\*\*|__[^_]+__|\[[^\]]+\]\([^)]+\)|\*[^*]+\*|_[^_]+_)/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
      return (
        <strong key={index} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a
          key={index}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 underline hover:text-blue-800"
        >
          {linkMatch[1]}
        </a>
      );
    }
    return part;
  });
}

export function FormattedMarkdown({ content }: FormattedMarkdownProps) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      elements.push(<div key={`br-${idx}`} className="h-1.5" />);
      return;
    }

    // Bullet list items
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      elements.push(
        <div key={idx} className="ml-3 flex items-start gap-2 my-0.5">
          <span className="text-blue-600 font-bold select-none">•</span>
          <div className="flex-1">{parseInline(trimmed.slice(2))}</div>
        </div>
      );
      return;
    }

    // Numbered list items
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      elements.push(
        <div key={idx} className="ml-3 flex items-start gap-2 my-0.5">
          <span className="text-blue-600 font-semibold select-none">{numMatch[1]}.</span>
          <div className="flex-1">{parseInline(numMatch[2])}</div>
        </div>
      );
      return;
    }

    // Headers
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h3 key={idx} className="font-bold text-slate-900 text-base mt-2 mb-1">
          {parseInline(trimmed.slice(4))}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(
        <h2 key={idx} className="font-bold text-slate-900 text-lg mt-3 mb-1 border-b border-slate-200 pb-1">
          {parseInline(trimmed.slice(3))}
        </h2>
      );
      return;
    }

    // Default paragraph line
    elements.push(
      <p key={idx} className="my-0.5 leading-relaxed">
        {parseInline(line)}
      </p>
    );
  });

  return <div className="space-y-0.5">{elements}</div>;
}
