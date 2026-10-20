import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

export interface FlowStep {
  title: string;
  description: string;
  badge: string;
  badgeBg: string;
  sourceLabel: string;
  targetLabel: string;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  curveY?: number;
  packetColor: string;
  startFrame: number;
  durationFrames: number;
}

const FLOW_STEPS: FlowStep[] = [
  {
    title: 'Bước 1: Client gửi câu hỏi qua Gateway',
    description: 'Sinh viên K21 gửi câu hỏi kèm JWT Token HS256: "Em bị điểm C môn Triết, GPA tính sao?"',
    badge: '1. User Request & Auth',
    badgeBg: '#06b6d4',
    sourceLabel: 'frontend/src/ (Web Client)',
    targetLabel: 'gateway/ (Kong 3.9.3)',
    startX: 230,
    startY: 450,
    endX: 430,
    endY: 450,
    packetColor: '#06b6d4',
    startFrame: 315,
    durationFrames: 170,
  },
  {
    title: 'Bước 2: Gateway xác thực & định tuyến đến Chatbot',
    description: 'Kong Gateway kiểm tra chữ ký số JWT, Rate Limiting và proxy an toàn vào nội bộ.',
    badge: '2. Gateway Routing',
    badgeBg: '#10b981',
    sourceLabel: 'gateway/kong.template.yml',
    targetLabel: 'services/academic_chatbot_service',
    startX: 450,
    startY: 450,
    endX: 800,
    endY: 180,
    curveY: 300,
    packetColor: '#10b981',
    startFrame: 495,
    durationFrames: 170,
  },
  {
    title: 'Bước 3: Tra cứu 2-Stage Semantic Cache trong Redis',
    description: 'Giai đoạn 1 Bi-Encoder (>=0.88) & Giai đoạn 2 Cross-Encoder (>=0.20) chặn đứng Semantic Drift.',
    badge: '3. 2-Stage Semantic Cache',
    badgeBg: '#ef4444',
    sourceLabel: 'services/academic_chatbot_service',
    targetLabel: 'Redis 7 Cache (:6379)',
    startX: 1100,
    startY: 180,
    endX: 1500,
    endY: 180,
    packetColor: '#ef4444',
    startFrame: 675,
    durationFrames: 340,
  },
  {
    title: 'Bước 4: Truy vấn Parent-Child Hybrid Search vào PostgreSQL',
    description: 'Kết hợp pgvector 1024d (Dense) và FTS (Sparse) qua Reciprocal Rank Fusion (RRF).',
    badge: '4. Hybrid Retrieval & RRF',
    badgeBg: '#3b82f6',
    sourceLabel: 'services/.../rag_service.py',
    targetLabel: 'db/schema_v2_hybrid_rag.sql',
    startX: 1100,
    startY: 200,
    endX: 1500,
    endY: 420,
    curveY: 310,
    packetColor: '#3b82f6',
    startFrame: 1035,
    durationFrames: 260,
  },
  {
    title: 'Bước 5: Sandwich Reordering & Đóng gói Context Sandbox',
    description: 'Tái sắp xếp [#1, #3, #5, ..., #4, #2] khắc phục Lost-in-the-Middle và chặn Prompt Injection.',
    badge: '5. Context Sandboxing',
    badgeBg: '#f59e0b',
    sourceLabel: 'db/ (Top Chunks)',
    targetLabel: 'services/.../query_filter.py',
    startX: 1500,
    startY: 420,
    endX: 1050,
    endY: 220,
    curveY: 320,
    packetColor: '#f59e0b',
    startFrame: 1305,
    durationFrames: 230,
  },
  {
    title: 'Bước 6: Self-RAG Streaming SSE phản hồi về Client',
    description: 'Suy ngẫm <thinking>, tính Arithmetic CoT và truyền trực tiếp câu trả lời từng chữ qua SSE.',
    badge: '6. SSE Streaming & Citations',
    badgeBg: '#6366f1',
    sourceLabel: 'services/academic_chatbot_service',
    targetLabel: 'frontend/src/ (ChatBox UI)',
    startX: 800,
    startY: 180,
    endX: 200,
    endY: 450,
    curveY: 200,
    packetColor: '#a855f7',
    startFrame: 1545,
    durationFrames: 270,
  },
];

export const DataFlowOverlay: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div className="absolute inset-0 pointer-events-none z-30">
      <svg className="w-full h-full">
        {FLOW_STEPS.map((step, idx) => {
          if (frame < step.startFrame) return null;

          // Animation progress
          const progress = interpolate(
            frame,
            [step.startFrame, step.startFrame + step.durationFrames],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );

          // Quadratic bezier interpolation for curved paths
          const ctrlX = (step.startX + step.endX) / 2;
          const ctrlY = step.curveY !== undefined ? step.curveY : (step.startY + step.endY) / 2;

          // Compute current packet (x, y) along bezier curve
          const t = progress;
          const currentX = (1 - t) * (1 - t) * step.startX + 2 * (1 - t) * t * ctrlX + t * t * step.endX;
          const currentY = (1 - t) * (1 - t) * step.startY + 2 * (1 - t) * t * ctrlY + t * t * step.endY;

          // Path SVG string
          const pathD = `M ${step.startX} ${step.startY} Q ${ctrlX} ${ctrlY} ${step.endX} ${step.endY}`;

          return (
            <g key={idx}>
              {/* Active Path highlight */}
              <path
                d={pathD}
                fill="none"
                stroke={step.packetColor}
                strokeWidth="4"
                strokeDasharray="8 6"
                className="opacity-80"
              />

              {/* Moving Glowing Packet */}
              <circle
                cx={currentX}
                cy={currentY}
                r={10}
                fill="#ffffff"
                stroke={step.packetColor}
                strokeWidth="4"
                style={{
                  filter: `drop-shadow(0 0 18px ${step.packetColor})`,
                }}
              />

              {/* Ripple aura around moving packet */}
              <circle
                cx={currentX}
                cy={currentY}
                r={22}
                fill="none"
                stroke={step.packetColor}
                strokeWidth="2"
                opacity={0.6}
              />
            </g>
          );
        })}
      </svg>

      {/* Floating Step Info Card on Top Right */}
      {(() => {
        // Find the active step based on frame
        const currentActiveStep =
          FLOW_STEPS.slice()
            .reverse()
            .find((s) => frame >= s.startFrame) || FLOW_STEPS[0];

        return (
          <div className="absolute bottom-20 left-8 right-8 flex items-center justify-between bg-slate-900/95 border border-slate-700/80 rounded-2xl p-4 backdrop-blur-xl shadow-2xl">
            <div className="flex items-center gap-4">
              <span
                className="px-3 py-1.5 rounded-lg text-xs font-bold text-white shadow-md"
                style={{ backgroundColor: currentActiveStep.badgeBg }}
              >
                {currentActiveStep.badge}
              </span>
              <div>
                <h4 className="text-sm font-bold text-slate-100">
                  {currentActiveStep.title}
                </h4>
                <p className="text-xs text-slate-300">
                  {currentActiveStep.description}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-950/80 px-3 py-2 rounded-xl border border-slate-800">
              <span className="text-emerald-400 font-semibold">{currentActiveStep.sourceLabel}</span>
              <span className="text-slate-500">──▶</span>
              <span className="text-cyan-400 font-semibold">{currentActiveStep.targetLabel}</span>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
