import React from 'react';
import {
  Globe,
  ShieldCheck,
  ShieldAlert,
  GitBranch,
  Binary,
  Database,
  Layers,
  Sparkles,
  Maximize2,
  FileCode,
  Radio,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';

interface InteractiveRAGPipelineMapProps {
  activeStep: number;
}

export const PIPELINE_NODES = [
  { id: 0, label: '0. Tổng Quan', short: 'Overview', icon: Globe, color: 'text-sky-400', border: 'border-sky-500' },
  { id: 1, label: '1. Kong Gateway', short: 'Port 8000', icon: ShieldCheck, color: 'text-indigo-400', border: 'border-indigo-500' },
  { id: 2, label: '2. Guardrail', short: 'Zero-Token', icon: ShieldAlert, color: 'text-rose-400', border: 'border-rose-500' },
  { id: 3, label: '3. Router/Rewriter', short: '7 Intents', icon: GitBranch, color: 'text-amber-400', border: 'border-amber-500' },
  { id: 4, label: '4. Bi-Encoder', short: '768d ONNX', icon: Binary, color: 'text-cyan-400', border: 'border-cyan-500' },
  { id: 5, label: '5. 2-Stage Cache', short: 'Redis/pgvector', icon: Database, color: 'text-emerald-400', border: 'border-emerald-500' },
  { id: 6, label: '6. Hybrid RRF', short: 'k=60', icon: Layers, color: 'text-blue-400', border: 'border-blue-500' },
  { id: 7, label: '7. Reranker', short: 'Quota 2-8', icon: Sparkles, color: 'text-violet-400', border: 'border-violet-500' },
  { id: 8, label: '8. Sandwich Reorder', short: 'U-Curve', icon: Maximize2, color: 'text-fuchsia-400', border: 'border-fuchsia-500' },
  { id: 9, label: '9. XML Sandboxing', short: '-60% Token', icon: FileCode, color: 'text-orange-400', border: 'border-orange-500' },
  { id: 10, label: '10. LLM Stream', short: 'SSE Output', icon: Radio, color: 'text-teal-400', border: 'border-teal-500' },
  { id: 11, label: '11. Self-RAG Gate', short: 'Write-Back', icon: CheckCircle2, color: 'text-green-400', border: 'border-green-500' },
];

export const InteractiveRAGPipelineMap: React.FC<InteractiveRAGPipelineMapProps> = ({ activeStep }) => {
  return (
    <div className="w-full bg-slate-900/95 border-2 border-slate-800 rounded-2xl p-2.5 shadow-xl font-mono">
      <div className="flex items-center justify-between gap-1 overflow-hidden">
        {PIPELINE_NODES.map((node, index) => {
          const Icon = node.icon;
          const isActive = activeStep === node.id;
          const isPast = activeStep > node.id;

          return (
            <React.Fragment key={node.id}>
              <div
                className={`flex-1 flex flex-col items-center justify-center py-1.5 px-1 rounded-xl transition-all duration-200 border ${
                  isActive
                    ? `bg-slate-800/90 ${node.border} shadow-lg shadow-cyan-500/20 scale-102`
                    : isPast
                    ? 'bg-slate-950/70 border-slate-800/80 opacity-80'
                    : 'bg-slate-950/40 border-slate-900 opacity-50'
                }`}
              >
                <div className="flex items-center gap-1">
                  <Icon
                    size={14}
                    className={isActive ? node.color : isPast ? 'text-slate-300' : 'text-slate-500'}
                  />
                  <span
                    className={`text-[11px] font-bold truncate ${
                      isActive ? 'text-white' : isPast ? 'text-slate-300' : 'text-slate-500'
                    }`}
                  >
                    {node.short}
                  </span>
                </div>
                <div
                  className={`text-[9px] mt-0.5 truncate ${
                    isActive ? node.color : 'text-slate-500'
                  }`}
                >
                  {node.label}
                </div>
              </div>

              {index < PIPELINE_NODES.length - 1 && (
                <div className="shrink-0 text-slate-700 px-0.5">
                  <ArrowRight size={10} className={isPast ? 'text-slate-500' : 'text-slate-800'} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
