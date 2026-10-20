import React from 'react';
import { useCurrentFrame } from 'remotion';
import {
  Bot, ShieldCheck, Cpu, Database, Zap, GitMerge, Layers, Lock,
  ArrowRight, CheckCircle2, Server, Globe, Terminal, Sparkles, Activity
} from 'lucide-react';

export const EndToEndRAGFlowDiagram: React.FC = () => {
  const frame = useCurrentFrame();

  // Highlight step in sync with Scene 2 sentences:
  // Sentence 2 (frames 762 - 1199): UI -> Kong Gateway -> Academic Chatbot Service (port 8002)
  // Sentence 3 (frames 1208 - 1525): Guardrail Check & Rewriter/Router (7 intents)
  // Sentence 4 (frames 1534 - 1906): Shared LLM Architecture (Zero-shot JSON)
  // Sentence 5 (frames 1914 - 2351): 2-Stage Cache, Hybrid RRF, Sandbox & SSE Stream
  const isGatewayStep = frame >= 760 && frame < 1205;
  const isGuardrailStep = frame >= 1205 && frame < 1530;
  const isSharedLLMStep = frame >= 1530 && frame < 1910;
  const isPipelineStep = frame >= 1910;

  return (
    <div className="w-full h-full flex flex-col justify-between p-5 bg-slate-950/90 border-2 border-slate-800 rounded-3xl shadow-2xl backdrop-blur-xl select-none font-sans">
      {/* Top Architecture Flow Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/90">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">
            <Activity size={18} />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-cyan-400 tracking-wider">
              KIẾN TRÚC THỰC TẾ TRONG CODEBASE &bull; LUỒNG YÊU CẦU END-TO-END
            </span>
            <h3 className="text-base font-black text-white">
              IUH Student Portal (UI) &rarr; Kong API Gateway &rarr; Academic Chatbot Service (FastAPI) &rarr; SSE Stream
            </h3>
          </div>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="px-3 py-1 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            Port 8000 &rarr; Port 8002
          </span>
          <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
            Zero False Positives
          </span>
        </div>
      </div>

      {/* Main Multi-Tier Request Journey */}
      <div className="grid grid-cols-12 gap-4 my-auto items-stretch">
        
        {/* TIER 1: CLIENT & GATEWAY (3 cols) */}
        <div className="col-span-3 flex flex-col gap-3 justify-between">
          {/* User Query UI */}
          <div className={`p-4 rounded-2xl bg-slate-900 border-2 transition-colors duration-300 shadow-xl ${
            isGatewayStep ? 'border-cyan-400 bg-slate-900/95 shadow-cyan-500/20' : 'border-slate-800'
          }`}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold">
                1. CLIENT TIER
              </span>
              <span className="text-[10px] font-mono text-slate-400">IUH Student Portal</span>
            </div>
            <h4 className="text-sm font-bold text-white flex items-center gap-1.5 mb-2">
              <Bot size={16} className="text-blue-400" /> Giao diện Sinh viên
            </h4>
            <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-amber-300 leading-snug">
              "Cảnh báo học vụ lần 1 học kỳ tới đăng ký tối đa bao nhiêu tín chỉ?"
            </div>
            <div className="mt-2 text-[10px] font-mono text-slate-400">
              POST /api/v1/chat/stream
            </div>
          </div>

          {/* Kong API Gateway */}
          <div className={`p-4 rounded-2xl bg-slate-900 border-2 transition-colors duration-300 shadow-xl ${
            isGatewayStep ? 'border-indigo-400 bg-indigo-950/20 shadow-indigo-500/20' : 'border-slate-800'
          }`}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold">
                2. KONG API GATEWAY
              </span>
              <span className="text-[10px] font-mono text-indigo-400 font-bold">Port 8000</span>
            </div>
            <h4 className="text-sm font-bold text-white flex items-center gap-1.5 mb-2">
              <ShieldCheck size={16} className="text-indigo-400" /> Cổng Bảo Mật &amp; Định Tuyến
            </h4>
            <div className="space-y-1 text-xs font-mono text-slate-300">
              <div className="p-1.5 rounded bg-slate-950 border border-slate-800 text-[11px]">
                &bull; <strong className="text-indigo-300">JWT Authentication:</strong> HS256 verify
              </div>
              <div className="p-1.5 rounded bg-slate-950 border border-slate-800 text-[11px]">
                &bull; <strong className="text-indigo-300">Rate Limiting:</strong> 1000 req/min
              </div>
              <div className="p-1.5 rounded bg-slate-950 border border-slate-800 text-[11px]">
                &bull; <strong className="text-indigo-300">Upstream:</strong> chatbot-upstream:8002
              </div>
            </div>
          </div>
        </div>

        {/* Central Connector Arrow */}
        <div className="col-span-1 flex flex-col items-center justify-center text-cyan-400">
          <div className="text-[10px] font-mono font-bold rotate-90 my-2 text-slate-500">HTTP REST</div>
          <ArrowRight size={24} className="text-cyan-400" />
        </div>

        {/* TIER 2: ACADEMIC CHATBOT SERVICE CORE PIPELINE (8 cols) */}
        <div className="col-span-8 flex flex-col justify-between p-4 rounded-2xl bg-slate-900/90 border-2 border-indigo-500/50 shadow-2xl">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Server size={18} className="text-indigo-400" />
              <span className="text-xs font-mono font-bold text-white">
                3. ACADEMIC CHATBOT SERVICE (FastAPI &bull; Port 8002 &bull; app/services/llm_generation_service.py)
              </span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
              Deterministic 1-Way Flow
            </span>
          </div>

          {/* Internal RAG Pipeline Grid */}
          <div className="grid grid-cols-4 gap-3 my-3">
            
            {/* Step A: Guardrail */}
            <div className={`p-3 rounded-xl bg-slate-950 border transition-colors duration-300 ${
              isGuardrailStep ? 'border-rose-400 shadow-lg shadow-rose-500/20' : 'border-slate-800'
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono text-rose-400 font-bold mb-1">
                <span>A. GUARDRAIL</span>
                <span>tests/unit/test_guardrails.py</span>
              </div>
              <h5 className="text-xs font-bold text-white mb-1">Chặn Tiêm Mã</h5>
              <p className="text-[11px] text-slate-300 leading-snug">
                Phát hiện thẻ đóng giả mạo <code>&lt;/retrieved_context&gt;</code> &amp; từ chối ngay tức thì.
              </p>
            </div>

            {/* Step B: Rewriter & Intent Router */}
            <div className={`p-3 rounded-xl bg-slate-950 border transition-colors duration-300 ${
              isGuardrailStep || isSharedLLMStep ? 'border-blue-400 shadow-lg shadow-blue-500/20' : 'border-slate-800'
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono text-blue-400 font-bold mb-1">
                <span>B. REWRITER</span>
                <span>Shared LLM</span>
              </div>
              <h5 className="text-xs font-bold text-white mb-1">7 Intents &amp; Sub-queries</h5>
              <p className="text-[11px] text-slate-300 leading-snug">
                Zero-shot JSON phân loại 7 ý định và rã câu hỏi kép thành tối đa 4 truy vấn con.
              </p>
            </div>

            {/* Step C: 2-Stage Semantic Cache */}
            <div className={`p-3 rounded-xl bg-slate-950 border transition-colors duration-300 ${
              isPipelineStep ? 'border-amber-400 shadow-lg shadow-amber-500/20' : 'border-slate-800'
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono text-amber-400 font-bold mb-1">
                <span>C. 2-STAGE CACHE</span>
                <span>12ms Redis</span>
              </div>
              <h5 className="text-xs font-bold text-white mb-1">Bộ Đệm Ngữ Nghĩa</h5>
              <p className="text-[11px] text-slate-300 leading-snug">
                Redis O(1) + pgvector 768d + Entity Numbers Guard chống nhầm lẫn năm học.
              </p>
            </div>

            {/* Step D: Hybrid RRF Search */}
            <div className={`p-3 rounded-xl bg-slate-950 border transition-colors duration-300 ${
              isPipelineStep ? 'border-emerald-400 shadow-lg shadow-emerald-500/20' : 'border-slate-800'
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono text-emerald-400 font-bold mb-1">
                <span>D. HYBRID RRF</span>
                <span>Postgres 16</span>
              </div>
              <h5 className="text-xs font-bold text-white mb-1">Song Song &amp; RRF (k=60)</h5>
              <p className="text-[11px] text-slate-300 leading-snug">
                Dense HNSW vector 768d kết hợp Sparse BM25; tài liệu đồng thuận luôn thắng.
              </p>
            </div>

          </div>

          {/* Post-Retrieval & Generation Bar */}
          <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-800 text-xs font-mono">
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <strong className="text-purple-400 block mb-0.5">E. Reranker &amp; Small-to-Big:</strong>
              <span className="text-slate-300 text-[11px]">BGE-Reranker chấm điểm chéo &bull; Quota 2-8 khối cha &bull; Bung 1200 token.</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <strong className="text-cyan-400 block mb-0.5">F. Sandwich &amp; XML Sandbox:</strong>
              <span className="text-slate-300 text-[11px]">Trị Lost-in-the-Middle [#1, #3, #5, #4, #2] &bull; Buồng cách ly XML an toàn.</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <strong className="text-emerald-400 block mb-0.5">G. LLM Output &amp; Quality Gate:</strong>
              <span className="text-slate-300 text-[11px]">SSE Stream từng token về UI &bull; Self-RAG reflection kiểm soát ghi đệm.</span>
            </div>
          </div>

          {/* Unified Model Note */}
          <div className="mt-2.5 p-2 rounded-xl bg-indigo-950/30 border border-indigo-500/30 flex items-center justify-between text-xs font-mono">
            <span className="text-indigo-300 font-bold">
              ✓ Mã nguồn dùng chung 1 LLM cho cả bước Rewriter &amp; bước Trả lời cuối cùng
            </span>
            <span className="text-emerald-400 font-bold">Server-Sent Events (SSE) Streaming</span>
          </div>
        </div>

      </div>

      {/* Bottom Status Footnote */}
      <div className="pt-2.5 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
        <span>Toàn bộ quy trình diễn ra khép kín, an toàn tuyệt đối và bảo vệ quyền lợi học tập của sinh viên IUH</span>
        <span className="text-emerald-400 font-bold">&bull; End-to-End Latency: 0.8s - 1.2s (Cache Hit: &lt; 15ms)</span>
      </div>
    </div>
  );
};
