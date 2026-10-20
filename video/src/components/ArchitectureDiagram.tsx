import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { ARCHITECTURE_NODES } from '../data/architectureData';
import {
  Bot,
  Cpu,
  Database,
  FileText,
  HardDrive,
  Key,
  Languages,
  Layout,
  Radio,
  ShieldCheck,
  Zap,
} from 'lucide-react';

interface Props {
  highlightNodeId?: string;
  activeCategory?: string;
  showDetails?: boolean;
}

const ICON_MAP: Record<string, React.FC<{ size?: number; color?: string; className?: string }>> = {
  Layout,
  ShieldCheck,
  Bot,
  Key,
  Languages,
  FileText,
  Cpu,
  Zap,
  Database,
  Radio,
  HardDrive,
};

export const ArchitectureDiagram: React.FC<Props> = ({
  highlightNodeId,
  activeCategory,
  showDetails = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle floating background animation
  const bgPulse = interpolate(Math.sin(frame / 20), [-1, 1], [0.15, 0.28]);

  return (
    <div className="relative w-full h-full bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      {/* Background Tech Grid */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(99, 102, 241, ${bgPulse}) 1px, transparent 0)`,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Atmospheric Glow in the center */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[550px] bg-indigo-900/20 blur-[140px] pointer-events-none rounded-full" />
      <div className="absolute top-1/4 right-1/4 w-[500px] h-[400px] bg-cyan-900/15 blur-[120px] pointer-events-none rounded-full" />

      {/* Category Tier Headers */}
      <div className="absolute top-8 left-0 right-0 flex justify-between px-16 pointer-events-none">
        <div className="text-center w-[16%]">
          <span className="text-xs font-semibold tracking-wider uppercase text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-3 py-1 rounded-full">
            Tier 1: Web Client
          </span>
        </div>
        <div className="text-center w-[16%]">
          <span className="text-xs font-semibold tracking-wider uppercase text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-3 py-1 rounded-full">
            Tier 2: API Gateway
          </span>
        </div>
        <div className="text-center w-[28%]">
          <span className="text-xs font-semibold tracking-wider uppercase text-indigo-400 bg-indigo-950/60 border border-indigo-800/60 px-3 py-1 rounded-full">
            Tier 3: Core AI Microservices
          </span>
        </div>
        <div className="text-center w-[16%]">
          <span className="text-xs font-semibold tracking-wider uppercase text-purple-400 bg-purple-950/60 border border-purple-800/60 px-3 py-1 rounded-full">
            Tier 4: Async Worker
          </span>
        </div>
        <div className="text-center w-[20%]">
          <span className="text-xs font-semibold tracking-wider uppercase text-blue-400 bg-blue-950/60 border border-blue-800/60 px-3 py-1 rounded-full">
            Tier 5: Data & Broker
          </span>
        </div>
      </div>

      {/* SVG Connecting Backplanes */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <linearGradient id="lineGradCyan" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="lineGradIndigo" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="lineGradPurple" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#f97316" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        {/* Client to Gateway */}
        <path
          d="M 230 450 L 400 450"
          stroke="url(#lineGradCyan)"
          strokeWidth="2.5"
          strokeDasharray="6 4"
          fill="none"
          className="opacity-70"
        />

        {/* Gateway to Chatbot */}
        <path
          d="M 520 450 C 650 450, 680 180, 800 180"
          stroke="url(#lineGradIndigo)"
          strokeWidth="2.5"
          fill="none"
          className="opacity-60"
        />
        {/* Gateway to Auth */}
        <path
          d="M 520 450 L 800 420"
          stroke="#10b981"
          strokeWidth="2"
          fill="none"
          className="opacity-50"
        />
        {/* Gateway to Realtime Trans */}
        <path
          d="M 520 450 C 650 450, 680 660, 800 660"
          stroke="#f59e0b"
          strokeWidth="2"
          fill="none"
          className="opacity-50"
        />
        {/* Gateway to Doc Translation */}
        <path
          d="M 520 450 C 650 450, 680 880, 800 880"
          stroke="#8b5cf6"
          strokeWidth="2"
          fill="none"
          className="opacity-50"
        />

        {/* Chatbot to Redis Cache */}
        <path
          d="M 1120 180 L 1500 180"
          stroke="#ef4444"
          strokeWidth="2.5"
          strokeDasharray="6 4"
          fill="none"
          className="opacity-75"
        />
        {/* Chatbot to Postgres DB */}
        <path
          d="M 1120 200 C 1280 200, 1340 420, 1500 420"
          stroke="#3b82f6"
          strokeWidth="2.5"
          fill="none"
          className="opacity-75"
        />

        {/* Doc Svc to RabbitMQ */}
        <path
          d="M 1120 880 C 1280 880, 1340 680, 1500 680"
          stroke="#f97316"
          strokeWidth="2.5"
          fill="none"
          className="opacity-60"
        />
        {/* RabbitMQ to Worker */}
        <path
          d="M 1500 690 C 1380 690, 1320 880, 1260 880"
          stroke="#ea580c"
          strokeWidth="2"
          strokeDasharray="4 4"
          fill="none"
          className="opacity-60"
        />
        {/* Worker to MinIO S3 */}
        <path
          d="M 1260 900 L 1500 930"
          stroke="#14b8a6"
          strokeWidth="2"
          fill="none"
          className="opacity-60"
        />
      </svg>

      {/* Render Node Cards */}
      {ARCHITECTURE_NODES.map((node, index) => {
        const IconComponent = ICON_MAP[node.iconName] || Bot;

        // Staggered entrance animation using spring
        const nodeDelay = index * 3;
        const scaleSpring = spring({
          frame: frame - nodeDelay,
          fps,
          config: { damping: 14, stiffness: 120 },
        });

        const isHighlighted = highlightNodeId === node.id;
        const isDimmed = highlightNodeId ? !isHighlighted : false;
        const isCatActive = activeCategory ? node.category === activeCategory : true;

        const opacity = isHighlighted ? 1 : isDimmed ? 0.22 : isCatActive ? 1 : 0.35;
        const transformScale = isHighlighted ? 1.12 : isDimmed ? 0.95 : 1;
        const zIndex = isHighlighted ? 50 : 10;

        return (
          <div
            key={node.id}
            style={{
              left: `${node.x}%`,
              top: `${node.y}%`,
              transform: `translate(-50%, -50%) scale(${scaleSpring * transformScale})`,
              opacity,
              zIndex,
              borderColor: isHighlighted ? '#facc15' : node.borderColor,
              boxShadow: isHighlighted
                ? `0 0 60px ${node.color}, 0 0 25px #facc15, 0 10px 40px rgba(0,0,0,0.8)`
                : `0 8px 32px rgba(0, 0, 0, 0.4)`,
              filter: isDimmed ? 'grayscale(30%)' : 'none',
            }}
            className={`absolute w-72 rounded-2xl p-4 border backdrop-blur-md ${
              isHighlighted ? 'ring-4 ring-amber-400 ring-offset-4 ring-offset-slate-950' : ''
            }`}
          >
            {/* Spotlight Focus Pill */}
            {isHighlighted && (
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-amber-400 text-slate-950 font-black text-[10px] px-3 py-0.5 rounded-full uppercase tracking-wider shadow-lg flex items-center gap-1">
                <span>🎯 ĐANG GIẢI THÍCH</span>
              </div>
            )}
            {/* Top row: Icon + Name + Port */}
            <div className="flex items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2.5">
                <div
                  className="p-2.5 rounded-xl flex items-center justify-center text-white"
                  style={{ backgroundColor: node.color }}
                >
                  <IconComponent size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-100 leading-tight">
                    {node.name}
                  </h3>
                  <p className="text-[11px] text-slate-400 font-medium">
                    {node.subTitle}
                  </p>
                </div>
              </div>

              {node.port && (
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900/90 text-slate-300 border border-slate-700">
                  {node.port}
                </span>
              )}
            </div>

            {node.isNewOrUpgraded && (
              <div className="mb-2">
                <span className="inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-indigo-400"
                    style={{
                      opacity: interpolate(Math.sin(frame / 8), [-1, 1], [0.3, 1]),
                    }}
                  />
                  Commit a50bcffd+ Upgraded
                </span>
              </div>
            )}

            {/* Bullet points / Features */}
            {showDetails && (
              <ul className="space-y-1 text-[11px] text-slate-300 border-t border-slate-800/80 pt-2">
                {node.details.map((detail, dIdx) => (
                  <li key={dIdx} className="flex items-start gap-1.5 leading-tight">
                    <span className="text-emerald-400 mt-0.5">▸</span>
                    <span>{detail}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
};
