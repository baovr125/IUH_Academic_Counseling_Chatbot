import React from 'react';
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { ImportantFile } from '../types';
import { CheckCircle2, Code2, Sparkles } from 'lucide-react';

interface Props {
  file: ImportantFile;
}

export const FileHighlightCard: React.FC<Props> = ({ file }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  const lines = file.codeSnippet.split('\n');

  return (
    <div
      style={{
        transform: `scale(${cardScale})`,
      }}
      className="w-full max-w-4xl bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl font-sans"
    >
      {/* Window Header */}
      <div className="bg-slate-950/80 px-5 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          <span className="ml-3 text-xs font-mono text-slate-400 flex items-center gap-1.5">
            <Code2 size={14} className="text-indigo-400" />
            {file.path}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className="text-[10px] font-bold px-2.5 py-0.5 rounded-full text-white flex items-center gap-1"
            style={{ backgroundColor: file.badgeColor }}
          >
            <Sparkles size={11} />
            {file.badge}
          </span>
        </div>
      </div>

      <div className="p-6 grid grid-cols-12 gap-6">
        {/* Left: Code Block (7 cols) */}
        <div className="col-span-7 bg-slate-950 rounded-xl p-4 border border-slate-800/90 font-mono text-[12px] leading-relaxed overflow-hidden">
          {lines.map((lineText, idx) => {
            const lineNum = idx + 1;
            const isHighlighted = file.highlightedLines?.includes(lineNum);

            return (
              <div
                key={idx}
                className={`flex items-start px-2 py-0.5 rounded ${
                  isHighlighted
                    ? 'bg-indigo-950/70 border-l-2 border-indigo-400 text-indigo-200 font-semibold'
                    : 'text-slate-300'
                }`}
              >
                <span className="w-8 select-none text-slate-600 text-right pr-3 text-[11px]">
                  {lineNum}
                </span>
                <span className="whitespace-pre overflow-x-auto">{lineText}</span>
              </div>
            );
          })}
        </div>

        {/* Right: Key Contributions & Description (5 cols) */}
        <div className="col-span-5 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: file.badgeColor }} />
              {file.fileName}
            </h3>
            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              {file.description}
            </p>

            <div className="space-y-2.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Đóng Góp Kỹ Thuật Chính:
              </span>
              {file.keyContributions.map((contrib, cIdx) => {
                const itemProgress = spring({
                  frame: frame - 10 - cIdx * 6,
                  fps,
                });
                return (
                  <div
                    key={cIdx}
                    style={{
                      opacity: itemProgress,
                      transform: `translateX(${(1 - itemProgress) * 20}px)`,
                    }}
                    className="flex items-start gap-2 bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/60"
                  >
                    <CheckCircle2 size={15} className="text-emerald-400 mt-0.5 shrink-0" />
                    <span className="text-xs text-slate-200 leading-tight">
                      {contrib}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400">
            <span>Folder: <code className="text-indigo-300">{file.folder}</code></span>
            <span className="text-emerald-400 font-semibold">100% Tested Passed</span>
          </div>
        </div>
      </div>
    </div>
  );
};
