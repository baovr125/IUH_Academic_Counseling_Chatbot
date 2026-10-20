import React from 'react';
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Folder, FileCode, ChevronRight, Sparkles } from 'lucide-react';

interface Props {
  activeFileIndex?: number;
  onSelectFile?: (index: number) => void;
}

export interface TreeItem {
  name: string;
  isFolder: boolean;
  level: number;
  highlightBadge?: string;
  badgeColor?: string;
  isOpen?: boolean;
}

const TREE_ITEMS: TreeItem[] = [
  { name: 'IUH_Academic_Counseling_Chatbot/', isFolder: true, level: 0, isOpen: true },
  
  // Gateway
  { name: 'gateway/', isFolder: true, level: 1, isOpen: true },
  { name: 'kong.template.yml', isFolder: false, level: 2, highlightBadge: 'JWT HS256 & Route Proxy', badgeColor: '#10b981' },
  
  // Frontend
  { name: 'frontend/', isFolder: true, level: 1, isOpen: true },
  { name: 'src/components/chat/ChatBox.tsx', isFolder: false, level: 2, highlightBadge: 'Regenerate Cache Bypass', badgeColor: '#06b6d4' },
  
  // Services
  { name: 'services/', isFolder: true, level: 1, isOpen: true },
  { name: 'academic_chatbot_service/', isFolder: true, level: 2, isOpen: true },
  { name: 'app/data_ingestion/chunkers/hybrid_chunker.py', isFolder: false, level: 3, highlightBadge: 'Parent-Child Chunking', badgeColor: '#10b981' },
  { name: 'app/services/rag_service.py', isFolder: false, level: 3, highlightBadge: 'Sandwich Reordering [#1, #3, ..., #2]', badgeColor: '#6366f1' },
  { name: 'app/prompts/prompt_templates.py', isFolder: false, level: 3, highlightBadge: 'SpatioRoute (-64% Token Prompt)', badgeColor: '#f59e0b' },
  { name: 'app/guardrails/query_filter.py', isFolder: false, level: 3, highlightBadge: 'Special Token & Injection Blocking', badgeColor: '#ef4444' },
  { name: 'app/services/llm_generation_service.py', isFolder: false, level: 3, highlightBadge: 'Self-RAG Reflection (<thinking>)', badgeColor: '#a855f7' },
  
  { name: 'auth_service/', isFolder: true, level: 2, isOpen: false },
  { name: 'realtime_translation_service/', isFolder: true, level: 2, isOpen: false },
  { name: 'doc_translation_service/', isFolder: true, level: 2, isOpen: false },
  { name: 'flashcard_service/', isFolder: true, level: 2, isOpen: false },
  
  // Database
  { name: 'db/', isFolder: true, level: 1, isOpen: true },
  { name: 'schema_v2_hybrid_rag.sql', isFolder: false, level: 2, highlightBadge: 'pgvector 1024d & RRF Hybrid Search', badgeColor: '#3b82f6' },
];

export const FolderTree: React.FC<Props> = ({ activeFileIndex = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div className="w-full h-full bg-slate-950/90 border border-slate-800 rounded-2xl p-5 shadow-2xl overflow-hidden font-mono text-xs select-none">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 text-slate-400">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Folder size={14} className="text-amber-400" />
          Project Repository Explorer
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800">
          commit a50bcffd..HEAD
        </span>
      </div>

      {/* Tree items */}
      <div className="space-y-1">
        {TREE_ITEMS.map((item, idx) => {
          const itemSpring = spring({
            frame: frame - idx * 2,
            fps,
          });

          const isItemActive =
            !item.isFolder && item.highlightBadge && idx % 4 === activeFileIndex % 4;

          return (
            <div
              key={idx}
              style={{
                opacity: itemSpring,
                transform: `translateX(${(1 - itemSpring) * 15}px)`,
                paddingLeft: `${item.level * 18}px`,
              }}
              className={`flex items-center justify-between py-1 px-2 rounded-lg ${
                isItemActive
                  ? 'bg-indigo-950/80 border border-indigo-500/80 text-white shadow-lg shadow-indigo-950'
                  : 'hover:bg-slate-900 text-slate-300'
              }`}
            >
              <div className="flex items-center gap-2 overflow-hidden truncate">
                {item.isFolder ? (
                  <>
                    <ChevronRight size={13} className="text-slate-500 shrink-0" />
                    <Folder size={15} className="text-amber-400 shrink-0" />
                  </>
                ) : (
                  <>
                    <span className="w-3" />
                    <FileCode
                      size={15}
                      className={isItemActive ? 'text-indigo-400 shrink-0' : 'text-slate-400 shrink-0'}
                    />
                  </>
                )}
                <span className={item.isFolder ? 'font-semibold text-slate-200' : 'text-slate-300'}>
                  {item.name}
                </span>
              </div>

              {item.highlightBadge && (
                <span
                  style={{
                    backgroundColor: `${item.badgeColor || '#6366f1'}22`,
                    borderColor: `${item.badgeColor || '#6366f1'}66`,
                    color: item.badgeColor || '#6366f1',
                  }}
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0 flex items-center gap-1 ${
                    isItemActive ? 'ring-2 ring-indigo-400 ring-offset-1 ring-offset-slate-950' : ''
                  }`}
                >
                  <Sparkles size={10} />
                  {item.highlightBadge}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
