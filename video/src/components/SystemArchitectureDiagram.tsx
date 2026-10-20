import React from 'react';
import { Server, Database, Cpu, Network, ShieldCheck, Zap, HardDrive, ArrowRight, Layers, Bot, UserCheck, Activity } from 'lucide-react';

export const SystemArchitectureDiagram: React.FC = () => {
  return (
    <div className="w-full h-full flex flex-col justify-between p-4 bg-slate-950/70 border-2 border-slate-800 rounded-3xl shadow-2xl backdrop-blur-xl">
      {/* Subtle compact label bar - not competing with main title */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <Network size={16} className="text-cyan-400" />
          <span className="text-xs font-mono font-bold text-slate-300">
            Microservices Architecture &bull; 5 Services &bull; Kong API Gateway &bull; Event-Driven
          </span>
        </div>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Production Ready
        </span>
      </div>

      {/* Main Microservices Diagram Grid */}
      <div className="grid grid-cols-12 gap-5 my-auto items-stretch">
        
        {/* Column 1: Client & Gateway (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4 justify-center">
          {/* Frontend Client */}
          <div className="p-4 rounded-2xl bg-slate-900 border-2 border-blue-500/50 shadow-xl flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
              <Bot size={22} />
            </div>
            <div>
              <div className="text-xs font-mono text-blue-400 font-bold uppercase">Client Tier</div>
              <h4 className="text-sm font-bold text-white">IUH Student Portal</h4>
              <p className="text-[11px] text-slate-400">Web App &bull; Mobile UI &bull; WebSocket</p>
            </div>
          </div>

          {/* Connection Line */}
          <div className="flex justify-center text-cyan-400 py-0.5">
            <div className="h-6 w-0.5 bg-gradient-to-b from-blue-500 to-cyan-500" />
          </div>

          {/* Kong Gateway */}
          <div className="p-4 rounded-2xl bg-gradient-to-b from-slate-900 to-cyan-950/40 border-2 border-cyan-500/60 shadow-xl shadow-cyan-500/10">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">API GATEWAY</span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold">Reverse Proxy</span>
            </div>
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck size={18} className="text-cyan-400" /> Kong Gateway
            </h4>
            <ul className="text-xs text-slate-300 mt-2 space-y-1 font-mono">
              <li>&bull; JWT Authentication &bull; SSL/TLS</li>
              <li>&bull; Rate Limiting (Token Bucket)</li>
              <li>&bull; Dynamic Path Routing (8001 / 8002)</li>
            </ul>
          </div>
        </div>

        {/* Central Arrow */}
        <div className="col-span-1 flex flex-col items-center justify-center text-cyan-400">
          <div className="text-xs font-mono font-bold rotate-90 my-2 text-slate-500">HTTP/REST</div>
          <ArrowRight size={28} className="text-cyan-400" />
        </div>

        {/* Column 2: Core Microservices (4 cols) */}
        <div className="col-span-4 flex flex-col gap-4 justify-center">
          
          {/* Service 1: Academic Chatbot Service (HERO SERVICE) */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/60 via-slate-900 to-blue-950/60 border-2 border-indigo-400 shadow-2xl shadow-indigo-500/20 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl pointer-events-none" />
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-indigo-500/30 text-indigo-300 font-bold border border-indigo-500/40">
                CORE MICROSERVICE &bull; PORT 8002
              </span>
              <span className="text-xs font-mono text-cyan-300 font-bold">FastAPI Async</span>
            </div>
            <h4 className="text-lg font-black text-white flex items-center gap-2">
              <Cpu size={20} className="text-indigo-400" /> Academic Chatbot Service
            </h4>
            <p className="text-xs text-slate-300 mt-1">Trái tim của hệ thống tư vấn học vụ thông minh</p>
            
            <div className="grid grid-cols-2 gap-2 mt-3 font-mono text-[11px]">
              <div className="p-2 rounded bg-slate-950/80 border border-slate-800 text-indigo-300">
                &bull; 2-Stage Semantic Cache
              </div>
              <div className="p-2 rounded bg-slate-950/80 border border-slate-800 text-indigo-300">
                &bull; Hybrid RRF Search (k=60)
              </div>
              <div className="p-2 rounded bg-slate-950/80 border border-slate-800 text-indigo-300">
                &bull; Sandwich Reorder
              </div>
              <div className="p-2 rounded bg-slate-950/80 border border-slate-800 text-indigo-300">
                &bull; SpatioRoute (-64% tok)
              </div>
            </div>
          </div>

          {/* Service 2: User Service */}
          <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
                <UserCheck size={18} />
              </div>
              <div>
                <h5 className="text-xs font-bold text-white">User Service &bull; Port 8001</h5>
                <p className="text-[11px] text-slate-400 font-mono">Quản lý sinh viên, xác thực JWT, phân quyền khóa học</p>
              </div>
            </div>
            <span className="text-[10px] font-mono text-purple-400 px-2 py-0.5 rounded bg-purple-500/10">Active</span>
          </div>

          {/* Service 3: Celery Worker */}
          <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                <Activity size={18} />
              </div>
              <div>
                <h5 className="text-xs font-bold text-white">Celery Worker &bull; Async Tasks</h5>
                <p className="text-[11px] text-slate-400 font-mono">Nạp cẩm nang người học, phân đoạn chunking, tạo vector ngầm</p>
              </div>
            </div>
            <span className="text-[10px] font-mono text-amber-400 px-2 py-0.5 rounded bg-amber-500/10">Background</span>
          </div>
        </div>

        {/* Central Arrow */}
        <div className="col-span-1 flex flex-col items-center justify-center text-cyan-400">
          <div className="text-xs font-mono font-bold rotate-90 my-2 text-slate-500">I/O DATA</div>
          <ArrowRight size={28} className="text-emerald-400" />
        </div>

        {/* Column 3: Storage & Model Layer (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4 justify-center">
          
          {/* Redis Cluster */}
          <div className="p-4 rounded-2xl bg-slate-900 border-2 border-red-500/40 shadow-xl">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-bold">IN-MEMORY</span>
              <span className="text-[10px] font-mono text-slate-400">&lt; 1ms O(1)</span>
            </div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap size={16} className="text-red-400" /> Redis Semantic Cache
            </h4>
            <p className="text-xs text-slate-300 mt-1">Lưu trữ cặp truy vấn - câu trả lời, Session State, Celery Broker.</p>
          </div>

          {/* PostgreSQL 16 pgvector */}
          <div className="p-4 rounded-2xl bg-slate-900 border-2 border-emerald-500/50 shadow-xl">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">DATABASE</span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold">ACID Compliant</span>
            </div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Database size={16} className="text-emerald-400" /> PostgreSQL 16 + pgvector
            </h4>
            <ul className="text-xs text-slate-300 mt-1.5 space-y-0.5 font-mono">
              <li>&bull; <span className="text-emerald-400 font-bold">VECTOR(768):</span> HNSW Cosine Index</li>
              <li>&bull; <span className="text-cyan-400 font-bold">tsvector:</span> Full-Text Search simple</li>
              <li>&bull; <span className="text-purple-400 font-bold">Parent Store:</span> 1200t Full Legal Docs</li>
            </ul>
          </div>

          {/* AI Models / In-house Inference */}
          <div className="p-4 rounded-2xl bg-slate-900 border-2 border-indigo-500/40 shadow-xl">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold">AI INFERENCE</span>
              <span className="text-[10px] font-mono text-slate-400">FP16 / ONNX</span>
            </div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Cpu size={16} className="text-indigo-400" /> AI Neural Models
            </h4>
            <p className="text-xs text-slate-300 mt-1">
              bkai-bi-encoder (768d) &bull; BGE-Reranker-v2-m3 &bull; Qwen-2.5 local
            </p>
          </div>

        </div>

      </div>

      {/* Footer Info inside diagram */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
        <span>Độ trễ toàn trình (End-to-end Latency): <strong className="text-emerald-400">0.8s - 1.2s</strong> (Cache Hit: <strong className="text-cyan-400">&lt; 5ms</strong>)</span>
        <span>Phục vụ đồng thời 5.000+ sinh viên cùng lúc</span>
      </div>
    </div>
  );
};
