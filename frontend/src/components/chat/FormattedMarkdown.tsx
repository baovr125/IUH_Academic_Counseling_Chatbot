import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface FormattedMarkdownProps {
  content: string;
}

export function FormattedMarkdown({ content }: FormattedMarkdownProps) {
  if (!content) return null;

  return (
    <div className="max-w-none break-words">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
        code(props: any) {
          const { children, className, node, ...rest } = props;
          const match = /language-(\w+)/.exec(className || '');
          return match ? (
            <SyntaxHighlighter
              {...rest}
              PreTag="div"
              children={String(children).replace(/\n$/, '')}
              language={match[1]}
              style={vscDarkPlus}
              className="rounded-md my-2"
            />
          ) : (
            <code {...rest} className="bg-black/10 rounded px-1 py-0.5 text-xs font-mono text-inherit">
              {children}
            </code>
          );
        },
        table({ node, ...props }: any) {
          return (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full border-collapse border border-black/20" {...props} />
            </div>
          );
        },
        th({ node, ...props }: any) {
          return <th className="border border-black/20 px-3 py-2 bg-black/5 font-semibold text-left" {...props} />;
        },
        td({ node, ...props }: any) {
          return <td className="border border-black/20 px-3 py-2" {...props} />;
        },
        a({ node, ...props }: any) {
          return <a className="underline hover:opacity-80 font-medium" target="_blank" rel="noopener noreferrer" {...props} />;
        },
        p({ node, ...props }: any) {
          return <p className="my-1.5 leading-relaxed" {...props} />;
        },
        ul({ node, ...props }: any) {
          return <ul className="list-disc ml-5 my-1.5 space-y-1" {...props} />;
        },
        ol({ node, ...props }: any) {
          return <ol className="list-decimal ml-5 my-1.5 space-y-1" {...props} />;
        },
        h2({ node, ...props }: any) {
          return <h2 className="font-bold text-lg mt-3 mb-1 border-b border-black/10 pb-1" {...props} />;
        },
        h3({ node, ...props }: any) {
          return <h3 className="font-bold text-base mt-2 mb-1" {...props} />;
        }
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  );
}
