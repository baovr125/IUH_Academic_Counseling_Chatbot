import React from 'react';
import { Audio, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import {
  Brain,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Server,
  Database,
  Cpu,
  Layers,
  Sparkles,
  GitBranch,
  Binary,
  Radio,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Table,
  Calculator,
  Scale,
  Maximize2,
  FileCode,
  FileCheck,
  Lock,
  ArrowRight,
  Globe,
  Terminal,
  Activity,
  Zap,
  Repeat
} from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { InteractiveRAGPipelineMap } from '../components/InteractiveRAGPipelineMap';
import timingsData from '../data/ragOperationTimings.json';

export const SceneRAGOperationFlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find active step based on exact frame ranges in ragOperationTimings.json
  const steps = timingsData.steps;
  let activeStep = 0;
  for (let i = 0; i < steps.length; i++) {
    if (frame >= steps[i].start_frame) {
      activeStep = steps[i].step_id;
    }
  }

  const currentStepData = steps[activeStep] || steps[0];

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/rag_operation_flow.mp3')} volume={1} />
      <AnimatedBackground theme="cyan" />

      {/* Main Container */}
      <div className="flex flex-col w-full h-full px-8 py-4 justify-between z-10">
        
        {/* 1. Header Bar with System Info and Step Indicator */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Cpu size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-cyan-400">
                  IUH ACADEMIC RAG CHATBOT • END-TO-END SYSTEM PIPELINE
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; {currentStepData.file}</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
                <span>{currentStepData.title}</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Bước {activeStep} / 11
                </span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-slate-300 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-slate-800">
              <Activity size={14} className="text-emerald-400" />
              <span>FastAPI Port 8002</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-indigo-400">Kong Port 8000</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-amber-400">Qwen-35B</span>
            </div>
          </div>
        </div>

        {/* 2. Interactive Pipeline Map (Always visible, active step highlights) */}
        <div className="my-1.5">
          <InteractiveRAGPipelineMap activeStep={activeStep} />
        </div>

        {/* 3. Main Stage Content Area (Fills ~75% useful screen area) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full max-w-[1780px] mx-auto">
          
          {/* STEP 0: TỔNG QUAN KIẾN TRÚC TOÀN TRÌNH */}
          {activeStep === 0 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-cyan-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30 flex items-center gap-1.5">
                    <Globe size={14} /> TỔNG QUAN HỆ THỐNG
                  </span>
                  <h3 className="text-2xl font-black text-white">Kiến Trúc Advanced RAG Phục Vụ Hơn 30.000 Sinh Viên IUH</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-xl border border-cyan-500/30">
                  Microservices Architecture
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                      <Server size={18} className="text-cyan-400" /> Luồng Xử Lý Khép Kín 1 Chiều
                    </h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Hệ thống loại bỏ hoàn toàn các vòng lặp tự trị đa tác tử (Agentic Loop) dễ gây tắc nghẽn, áp dụng luồng xác định (Deterministic Pipeline) với độ trễ phản hồi đệm dưới <strong>15ms</strong> và truy xuất sâu dưới <strong>1.2 giây</strong>.
                    </p>

                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                        <span className="text-slate-400">1. Client Tier:</span>
                        <span className="text-white font-bold">Portal Sinh viên (React/Tailwind)</span>
                      </div>
                      <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                        <span className="text-slate-400">2. Gateway Tier:</span>
                        <span className="text-indigo-400 font-bold">Kong Gateway (Port 8000)</span>
                      </div>
                      <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                        <span className="text-slate-400">3. Core Service:</span>
                        <span className="text-cyan-400 font-bold">academic_chatbot_service (Port 8002)</span>
                      </div>
                      <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                        <span className="text-slate-400">4. Data Tier:</span>
                        <span className="text-emerald-400 font-bold">PostgreSQL 16 + pgvector + Redis</span>
                      </div>
                      <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                        <span className="text-slate-400">5. Shared LLM:</span>
                        <span className="text-amber-400 font-bold">Qwen3.6-35B-A3B-AWQ (vLLM)</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl text-xs text-cyan-200">
                    &bull; Đảm bảo độ chính xác quy chế học vụ tuyệt đối, không suy diễn cảm tính.
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                      <Layers size={18} className="text-emerald-400" /> Sơ Đồ Khối Thực Tế Trong Codebase
                    </h4>
                    
                    {/* Visual End-to-End Diagram Box */}
                    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-4 font-mono text-xs space-y-3">
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div className="p-3 bg-sky-950/50 border border-sky-500/40 rounded-xl">
                          <div className="font-bold text-sky-300">1. Client / Portal</div>
                          <div className="text-[10px] text-slate-400 mt-1">Câu hỏi: Bị cảnh báo lần 1 đăng ký tối đa mấy tín chỉ?</div>
                        </div>
                        <div className="p-3 bg-indigo-950/50 border border-indigo-500/40 rounded-xl">
                          <div className="font-bold text-indigo-300">2. Kong Gateway</div>
                          <div className="text-[10px] text-slate-400 mt-1">Rate Limit 1000/phút • X-Request-ID • Reverse Proxy</div>
                        </div>
                        <div className="p-3 bg-cyan-950/50 border border-cyan-500/40 rounded-xl">
                          <div className="font-bold text-cyan-300">3. Chatbot Service</div>
                          <div className="text-[10px] text-slate-400 mt-1">FastAPI • 11 Bước Xử Lý Kỹ Thuật Chuyên Sâu</div>
                        </div>
                      </div>

                      <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                        <div className="text-xs font-bold text-amber-400 flex items-center justify-between">
                          <span>Các Chốt Chặn Kỹ Thuật Cốt Lõi Bên Trong Service:</span>
                          <span className="text-[10px] text-slate-500">app/services/rag_service.py</span>
                        </div>
                        <div className="grid grid-cols-4 gap-2 text-[10px] text-slate-300">
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Guardrail Regex</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Qwen Rewriter 7 Ý Định</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; 2-Stage Cache (12ms)</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Bi-Encoder 768d ONNX</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Hybrid RRF (k=60)</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Cross-Encoder Reranker</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Sandwich Permutation</div>
                          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">&bull; Self-RAG Quality Gate</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3.5 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-emerald-300">
                    <span>100% Khớp với mã nguồn triển khai thực tế của dự án tốt nghiệp</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 1: KONG GATEWAY */}
          {activeStep === 1 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-indigo-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30 flex items-center gap-1.5">
                    <ShieldCheck size={14} /> BƯỚC 1: CỔNG BẢO MẬT &amp; ĐỊNH TUYẾN
                  </span>
                  <h3 className="text-2xl font-black text-white">Kong API Gateway (Port 8000 &rarr; Port 8002)</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-xl border border-cyan-500/30">
                  gateway/kong.template.yml
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">4 Chính Sách Bảo Mật Gateway Cốt Lõi</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Mọi request từ Portal sinh viên đều phải đi qua Kong Gateway, ngăn ngừa tấn công DoS, giả mạo danh tính và bảo vệ các dịch vụ nội bộ.
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-indigo-400 font-bold flex items-center gap-1.5 mb-1">
                          <Activity size={14} /> 1. Rate Limiting: 1.000 req/min
                        </div>
                        <div className="text-[11px] text-slate-400">Chặn đứng hành vi spam hoặc tấn công từ chối dịch vụ.</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-cyan-400 font-bold flex items-center gap-1.5 mb-1">
                          <Code2 size={14} /> 2. Correlation ID (X-Request-ID)
                        </div>
                        <div className="text-[11px] text-slate-400">Gán mã UUID duy nhất để truy vết toàn trình qua các container.</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-amber-400 font-bold flex items-center gap-1.5 mb-1">
                          <Lock size={14} /> 3. Request Transformer (Strip Headers)
                        </div>
                        <div className="text-[11px] text-slate-400">Tước bỏ các header client tự khai báo (X-User-ID, X-User-Role).</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-emerald-400 font-bold flex items-center gap-1.5 mb-1">
                          <Server size={14} /> 4. Upstream Healthcheck
                        </div>
                        <div className="text-[11px] text-slate-400">Cân bằng tải least-connections và giám sát chủ động /health.</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-[11px] font-mono text-indigo-300">
                    Forwarding: <code>/api/v1/chat/* &rarr; academic-chatbot-service:8002</code>
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Cấu Hình Khai Báo Trong kong.template.yml</h4>
                    <div className="bg-slate-900/95 rounded-2xl border border-slate-800 p-4 font-mono text-xs text-slate-200 space-y-1.5 leading-relaxed">
                      <div className="text-slate-500"># Trích xuất từ gateway/kong.template.yml:</div>
                      <div><span className="text-indigo-400">upstreams:</span></div>
                      <div className="pl-4">- name: <span className="text-emerald-300">chatbot-upstream</span></div>
                      <div className="pl-6">algorithm: <span className="text-amber-300">least-connections</span></div>
                      <div className="pl-6">healthchecks: <span className="text-slate-400">http_path: /health</span></div>
                      <div><span className="text-indigo-400">services:</span></div>
                      <div className="pl-4">- name: <span className="text-emerald-300">academic-chatbot-service</span></div>
                      <div className="pl-6">host: <span className="text-cyan-300">chatbot-upstream</span></div>
                      <div className="pl-6">port: <span className="text-purple-300 font-bold">8002</span></div>
                      <div className="pl-6">routes:</div>
                      <div className="pl-8">- paths: [<span className="text-emerald-300">"/api/v1/chat"</span>, <span className="text-emerald-300">"/api/chat"</span>]</div>
                      <div><span className="text-indigo-400">plugins:</span></div>
                      <div className="pl-4">- name: <span className="text-amber-300">rate-limiting</span> (minute: 1000)</div>
                      <div className="pl-4">- name: <span className="text-amber-300">correlation-id</span> (header_name: X-Request-ID)</div>
                      <div className="pl-4">- name: <span className="text-rose-400">request-transformer</span> (remove: [X-User-ID, X-User-Role])</div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-indigo-950/30 border border-indigo-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-indigo-300">
                    <span>Mọi truy vấn đi vào dịch vụ đều được bảo vệ và chuẩn hóa 100%</span>
                    <ShieldCheck size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 2: GUARDRAIL */}
          {activeStep === 2 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-rose-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30 flex items-center gap-1.5">
                    <ShieldAlert size={14} /> BƯỚC 2: GUARDRAIL AN TOÀN
                  </span>
                  <h3 className="text-2xl font-black text-white">Chốt Chặn Kiểm Tra Chuỗi Câu Hỏi: 0 Token Cost</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-xl border border-cyan-500/30">
                  app/guardrails/query_filter.py
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Hệ Thống Regex Biên Dịch Sẵn</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Hàm <code>check_safety_and_jailbreak()</code> kiểm tra chuỗi đầu vào ngay lập tức bằng các biểu thức chính quy (Compiled Regex) trước khi chạm tới LLM, triệt tiêu 100% nguy cơ tấn công tiêm mã.
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-rose-950/40 border border-rose-500/40 rounded-xl">
                        <div className="text-rose-300 font-bold mb-1">1. Mẫu Tiêm Mã Jailbreak:</div>
                        <div className="text-[11px] text-slate-300">
                          <code>ignore previous instructions, DAN mode, sudo mode, lệnh từ phòng đào tạo, cập nhật hệ thống...</code>
                        </div>
                      </div>

                      <div className="p-3 bg-rose-950/40 border border-rose-500/40 rounded-xl">
                        <div className="text-rose-300 font-bold mb-1">2. Mẫu Phá Vỡ Cấu Trúc XML:</div>
                        <div className="text-[11px] text-slate-300">
                          <code>&lt;/retrieved_context&gt;, &lt;source&gt;, &lt;thinking&gt;, &lt;doc_relevance&gt;, &lt;|im_start|&gt;</code>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3.5 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl text-xs font-mono text-emerald-300">
                    &bull; Phát hiện vi phạm: Trả về REFUSAL_MESSAGE tức thì, tiết kiệm 100% chi phí gọi mô hình.
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Mã Nguồn Xử Lý An Toàn</h4>
                    <div className="bg-slate-900/95 rounded-2xl border border-slate-800 p-4 font-mono text-xs text-slate-200 space-y-1.5 leading-relaxed">
                      <div className="text-slate-500"># Trích xuất từ app/guardrails/query_filter.py:</div>
                      <div><span className="text-purple-400 font-bold">def</span> <span className="text-cyan-300 font-bold">check_safety_and_jailbreak</span>(query: str) -&gt; Optional[str]:</div>
                      <div className="pl-4"><span className="text-purple-400">if not</span> query: <span className="text-purple-400">return None</span></div>
                      <div className="pl-4"><span className="text-purple-400">for</span> pattern <span className="text-purple-400">in</span> COMPILED_JAILBREAK_REGEX:</div>
                      <div className="pl-8"><span className="text-purple-400">if</span> pattern.search(query):</div>
                      <div className="pl-12 text-rose-400 font-bold"><span className="text-purple-400">return</span> REFUSAL_MESSAGE  <span className="text-slate-500"># Chặn đứng 0 token!</span></div>
                      <div className="pl-4"><span className="text-purple-400">return None</span></div>
                    </div>

                    <div className="mt-3 p-3 bg-slate-900 rounded-2xl border border-slate-800 text-[11px] font-mono text-slate-300">
                      <strong>Phản hồi an toàn:</strong> "⚠️ Cảnh báo an toàn: Câu lệnh của bạn chứa từ ngữ hoặc mục đích can thiệp hệ thống không phù hợp. Vui lòng chỉ đặt câu hỏi liên quan đến học vụ IUH."
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-rose-950/30 border border-rose-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-rose-300">
                    <span>100% Ca kiểm thử Unit Test `test_guardrails.py` vượt qua</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 3: REWRITER & ROUTER */}
          {activeStep === 3 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-amber-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30 flex items-center gap-1.5">
                    <GitBranch size={14} /> BƯỚC 3: ĐỊNH TUYẾN &amp; PHÂN RÃ
                  </span>
                  <h3 className="text-2xl font-black text-white">Mô Hình Dùng Chung Qwen-35B: 7 Ý Định &amp; Rã Câu Hỏi</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-xl border border-cyan-500/30">
                  generate_standalone_query()
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Phân Loại Chính Xác 7 Nhóm Ý Định Học Vụ</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      Thay vì sử dụng một mô hình riêng biệt gây tốn VRAM, hệ thống dùng chung mô hình <strong>QuantTrio/Qwen3.6-35B-A3B-AWQ</strong> để phân loại ý định và phân rã câu hỏi kép thành tối đa 4 truy vấn độc lập:
                    </p>

                    <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                      <div className="p-2 bg-slate-900 border border-slate-800 rounded-lg">
                        <span className="text-amber-400 font-bold">1. PROCEDURE</span>
                        <div className="text-[10px] text-slate-400 mt-0.5">Thủ tục bảo lưu, rút hồ sơ, chuyển ngành.</div>
                      </div>
                      <div className="p-2 bg-emerald-950/40 border border-emerald-500/40 rounded-lg">
                        <span className="text-emerald-300 font-bold">2. REGULATION</span>
                        <div className="text-[10px] text-slate-300 mt-0.5">Quy chế đào tạo, tín chỉ, chuẩn đầu ra.</div>
                      </div>
                      <div className="p-2 bg-rose-950/40 border border-rose-500/40 rounded-lg">
                        <span className="text-rose-300 font-bold">3. CRISIS</span>
                        <div className="text-[10px] text-slate-300 mt-0.5">Khủng hoảng tâm lý/học tập, hotline tư vấn.</div>
                      </div>
                      <div className="p-2 bg-slate-900 border border-slate-800 rounded-lg">
                        <span className="text-cyan-400 font-bold">4. ADVISING</span>
                        <div className="text-[10px] text-slate-400 mt-0.5">Tư vấn chọn môn, lộ trình học tập.</div>
                      </div>
                      <div className="p-2 bg-slate-900 border border-slate-800 rounded-lg">
                        <span className="text-slate-300 font-bold">5. COMPLAINT</span>
                        <div className="text-[10px] text-slate-400 mt-0.5">Khiếu nại điểm, phúc khảo bài thi.</div>
                      </div>
                      <div className="p-2 bg-slate-900 border border-slate-800 rounded-lg">
                        <span className="text-slate-300 font-bold">6. TECH &amp; 7. GENERAL</span>
                        <div className="text-[10px] text-slate-400 mt-0.5">Lỗi portal, câu hỏi xã giao chào hỏi.</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-2.5 bg-amber-950/30 border border-amber-500/30 rounded-xl text-xs font-mono text-amber-300">
                    &bull; Câu hỏi xã giao / cảm ơn: Đặt <code>need_retrieval=false</code>, bỏ qua RAG để trả lời tức thì!
                  </div>
                </div>

                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Ví Dụ Phân Rã Câu Hỏi Kép Thực Tế</h4>
                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <span className="text-slate-400">Câu hỏi của sinh viên:</span>
                        <div className="text-white font-bold mt-1">
                          "Em muốn bảo lưu kỳ này và rút học phí thì làm thế nào?"
                        </div>
                      </div>

                      <div className="p-3 bg-slate-900/90 rounded-xl border border-emerald-500/40 text-[11px] space-y-1">
                        <div className="text-emerald-400 font-bold">JSON Phân Tích Từ Rewriter:</div>
                        <div className="text-slate-300">{`{`}</div>
                        <div className="pl-4 text-cyan-300">"need_retrieval": true,</div>
                        <div className="pl-4 text-amber-300">"intent": "PROCEDURE",</div>
                        <div className="pl-4 text-purple-300">"queries": [</div>
                        <div className="pl-8 text-emerald-300">"điều kiện hồ sơ xin tạm dừng tiến độ học tập bảo lưu kết quả",</div>
                        <div className="pl-8 text-emerald-300">"quy định rút và hoàn trả học phí khi tạm dừng học tập"</div>
                        <div className="pl-4 text-purple-300">]</div>
                        <div className="text-slate-300">{`}`}</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-emerald-300">
                    <span>Tách câu hỏi kép giúp tra cứu độc lập chính xác 100% cả 2 vế</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 4: BI-ENCODER & HYBRID MEMORY */}
          {activeStep === 4 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-cyan-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30 flex items-center gap-1.5">
                    <Binary size={14} /> BƯỚC 4: MÃ HÓA VECTOR &amp; KÝ ỨC HỘI THOẠI
                  </span>
                  <h3 className="text-2xl font-black text-white">Vietnamese Bi-Encoder (768d) ONNX &amp; Ký Ức Ngữ Cảnh</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-xl border border-cyan-500/30">
                  CUDAExecutionProvider &bull; TTLCache
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Tối Ưu Hóa Vector Hóa Bằng ONNX Runtime</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Mô hình <strong>bkai-foundation-models/vietnamese-bi-encoder</strong> được xuất sang định dạng ONNX chạy trên nhân CUDA, giảm độ trễ sinh vector xuống dưới <strong>10ms</strong>.
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-cyan-400 font-bold mb-1">1. TTLCache Cục Bộ (In-Memory):</div>
                        <div className="text-[11px] text-slate-400">
                          <code>_embedding_cache = TTLCache(maxsize=500, ttl=1800)</code><br />
                          Tái sử dụng vector của các câu hỏi lặp lại ngay trong RAM.
                        </div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-emerald-400 font-bold mb-1">2. Cập Nhật Ký Ức Dài Hạn Bất Đồng Bộ:</div>
                        <div className="text-[11px] text-slate-400">
                          <code>asyncio.create_task(update_message_embedding_in_db(...))</code><br />
                          Lưu vector của sinh viên vào DB mà không làm chậm luồng chính.
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-[11px] font-mono text-cyan-300">
                    &bull; Vector 768 chiều được chuẩn hóa L2 sẵn sàng cho tìm kiếm Cosine Similarity.
                  </div>
                </div>

                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Trích Xuất Ký Ức Ngữ Cảnh Dài Hạn</h4>
                    <div className="bg-slate-900/95 rounded-2xl border border-slate-800 p-4 font-mono text-xs text-slate-200 space-y-2 leading-relaxed">
                      <div className="text-slate-500"># Hàm trích xuất ký ức quá khứ (retrieve_past_memory):</div>
                      <div>res = supabase.rpc(<span className="text-emerald-300">"match_past_messages"</span>, &#123;</div>
                      <div className="pl-4"><span className="text-cyan-300">"query_vec"</span>: primary_embedding,</div>
                      <div className="pl-4"><span className="text-cyan-300">"match_threshold"</span>: <span className="text-purple-300">0.80</span>,</div>
                      <div className="pl-4"><span className="text-cyan-300">"p_session_id"</span>: session_id</div>
                      <div>&#125;).execute()</div>
                      
                      <div className="pt-2 border-t border-slate-800 text-[11px] text-amber-300">
                        [KÝ ỨC DÀI HẠN TỪ LỊCH SỬ CHAT TRƯỚC ĐÂY KHỚP VỚI NGỮ CẢNH]<br />
                        - Sinh viên từng nói: "Em học ngành Công nghệ Thông tin K19"<br />
                        &rArr; Tự động áp dụng quy chế K19 cho câu hỏi hiện tại!
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-cyan-300">
                    <span>Kết hợp hoàn hảo giữa Ký ức ngắn hạn và Ký ức ngữ nghĩa dài hạn</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 5: 2-STAGE SEMANTIC CACHE */}
          {activeStep === 5 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-emerald-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30 flex items-center gap-1.5">
                    <Database size={14} /> BƯỚC 5: BỘ ĐỆM NGỮ NGHĨA HAI GIAI ĐOẠN
                  </span>
                  <h3 className="text-2xl font-black text-white">2-Stage Semantic Cache &amp; Lớp Giáp Entity Numbers Guard</h3>
                </div>
                <span className="text-xs font-mono text-emerald-300 font-bold bg-emerald-950/60 px-3 py-1 rounded-xl border border-emerald-500/30">
                  Phản Hồi 12ms &bull; Tiết Kiệm 100% Chi Phí
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Quy Trình Kiểm Tra Đệm Đa Lớp</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      Để đối phó với hàng nghìn câu hỏi giống nhau trong mùa đăng ký học phần, hệ thống thiết lập bộ đệm 2 giai đoạn:
                    </p>

                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800">
                        <span className="text-emerald-400 font-bold">Lớp 0: Redis O(1) [12ms]</span>
                        <div className="text-[10px] text-slate-400">Khóa chuẩn hóa chuỗi text, trả kết quả tức thì.</div>
                      </div>

                      <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800">
                        <span className="text-cyan-400 font-bold">Lớp 1: pgvector Cosine (Ngưỡng 0.60)</span>
                        <div className="text-[10px] text-slate-400">Bi-Encoder quét nhanh ứng viên câu hỏi đồng nghĩa.</div>
                      </div>

                      <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800">
                        <span className="text-purple-400 font-bold">Lớp 2: Cross-Encoder BGE (Ngưỡng 0.80)</span>
                        <div className="text-[10px] text-slate-400">Kiểm định tương đồng ngữ nghĩa sâu nghiêm ngặt.</div>
                      </div>

                      <div className="p-2.5 bg-amber-950/30 border border-amber-500/40 rounded-xl">
                        <span className="text-amber-300 font-bold">Lớp Giáp: Entity Numbers Guard</span>
                        <div className="text-[10px] text-slate-300">So khớp chính xác từng con số (năm học, học kỳ, điểm GPA).</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-[11px] font-mono text-emerald-400 font-bold">
                    &bull; Cache Hit: Trả kết quả ngay lập tức, bỏ qua hoàn toàn bước Retrieval và LLM.
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Thực Nghiệm Chống Nhầm Lẫn Bằng Entity Guard</h4>
                    <div className="space-y-3 font-mono text-xs">
                      {/* Rejected case */}
                      <div className="p-3 bg-rose-950/30 border border-rose-500/40 rounded-2xl">
                        <div className="flex items-center justify-between text-rose-400 font-bold mb-1">
                          <span>Ca Bị Chặn: Lệch số năm học (Cosine: 0.98)</span>
                          <span className="text-[10px] bg-rose-900/60 px-2 py-0.5 rounded">BÁC BỎ CACHE</span>
                        </div>
                        <div className="text-[11px] text-slate-300 space-y-0.5">
                          <div>User: "Học phí K19 năm <span className="text-amber-300 font-bold underline">2025</span>" &rarr; Số: [19, 2025]</div>
                          <div>Cache: "Học phí K19 năm <span className="text-rose-400 font-bold underline">2024</span>" &rarr; Số: [19, 2024]</div>
                          <div className="text-rose-300 pt-1 font-bold">&rArr; 2025 != 2024: Entity Guard từ chối trả cache! Ép chạy RAG mới.</div>
                        </div>
                      </div>

                      {/* Accepted case */}
                      <div className="p-3 bg-emerald-950/30 border border-emerald-500/40 rounded-2xl">
                        <div className="flex items-center justify-between text-emerald-400 font-bold mb-1">
                          <span>Ca Hợp Lệ: Trùng khớp chính xác con số thực thể</span>
                          <span className="text-[10px] bg-emerald-900/60 px-2 py-0.5 rounded">TRẢ CACHE 12MS</span>
                        </div>
                        <div className="text-[11px] text-slate-300 space-y-0.5">
                          <div>User: "Cảnh báo học vụ lần <span className="text-emerald-300 font-bold underline">1</span> tối đa mấy tín?" &rarr; Số: [1]</div>
                          <div>Cache: "Cảnh báo học vụ lần <span className="text-emerald-300 font-bold underline">1</span> được đăng ký bao nhiêu tín?" &rarr; Số: [1]</div>
                          <div className="text-emerald-300 pt-1 font-bold">&rArr; Trùng số 1 + Cross-Encoder 0.92 &rarr; TRẢ LỜI NGAY LẬP TỨC!</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-emerald-300">
                    <span>Tuyệt đối không xảy ra hiện tượng trả nhầm thông tin năm học cũ</span>
                    <ShieldCheck size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 6: HYBRID RRF */}
          {activeStep === 6 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-blue-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30 flex items-center gap-1.5">
                    <Layers size={14} /> BƯỚC 6: TRUY XUẤT LAI HỢP SONG SONG
                  </span>
                  <h3 className="text-2xl font-black text-white">Hybrid RRF: PostgreSQL 16 HNSW (Dense) + BM25 (Sparse)</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-xl border border-cyan-500/30">
                  k = 60 &bull; 50 Candidates / Query
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Truy Xuất Song Song Đa Luồng</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Hệ thống thực thi đồng thời hàm RPC <code>match_chunks_hybrid_rrf</code> cho tất cả các sub-queries bằng <code>asyncio.gather</code>, dung hợp 2 trường phái tìm kiếm:
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-cyan-400 font-bold mb-1">Kênh Dense (Chỉ mục pgvector HNSW):</div>
                        <div className="text-[11px] text-slate-400">Tìm kiếm tương đồng ngữ nghĩa vector 768 chiều, hiểu ngữ cảnh và từ đồng nghĩa.</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-emerald-400 font-bold mb-1">Kênh Sparse (Chỉ mục BM25 / tsvector):</div>
                        <div className="text-[11px] text-slate-400">Tìm kiếm từ khóa chính xác tuyệt đối như tên mã môn, số quyết định, phòng ban.</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-blue-950/30 border border-blue-500/30 rounded-2xl text-xs font-mono text-blue-300">
                    Công thức RRF: <code>Score(d) = &sum; [ 1 / (60 + rank_i(d)) ]</code>
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Chứng Minh Toán Học: Sự Vượt Trội Của Đồng Thuận</h4>
                    
                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3.5 bg-slate-900 rounded-2xl border border-emerald-500/40">
                        <div className="flex items-center justify-between text-emerald-400 font-bold mb-1.5">
                          <span>Tài Liệu A (Được CẢ HAI KÊNH đồng thuận ở Hạng 2):</span>
                          <span className="text-[10px] bg-emerald-950 px-2 py-0.5 rounded text-emerald-300 font-bold">CHIẾN THẮNG</span>
                        </div>
                        <div className="text-slate-300 text-[11px] space-y-1">
                          <div>&bull; Rank Dense = 2 &rarr; 1 / (60 + 2) = 0.0161</div>
                          <div>&bull; Rank Sparse = 2 &rarr; 1 / (60 + 2) = 0.0161</div>
                          <div className="text-emerald-300 font-bold text-sm pt-1 border-t border-slate-800">
                            &rArr; Tổng Điểm RRF: 0.0161 + 0.0161 = 0.0322 Điểm
                          </div>
                        </div>
                      </div>

                      <div className="p-3.5 bg-slate-900 rounded-2xl border border-slate-800">
                        <div className="flex items-center justify-between text-slate-400 font-bold mb-1.5">
                          <span>Tài Liệu B (Chỉ đứng đầu ĐƠN ĐỘC ở Kênh Dense, vắng mặt ở Sparse):</span>
                          <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">THUA ĐIỂM</span>
                        </div>
                        <div className="text-slate-400 text-[11px] space-y-1">
                          <div>&bull; Rank Dense = 1 &rarr; 1 / (60 + 1) = 0.0163</div>
                          <div>&bull; Rank Sparse = Không lọt top (None) &rarr; 0.0000</div>
                          <div className="text-slate-300 font-bold text-sm pt-1 border-t border-slate-800">
                            &rArr; Tổng Điểm RRF: 0.0163 Điểm
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-blue-950/30 border border-blue-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-blue-300">
                    <span>Điểm đồng thuận 0.0322 gần gấp đôi 0.0163, triệt tiêu thiên vị thuật toán cục bộ</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 7: RERANKER & QUOTA */}
          {activeStep === 7 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-violet-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-violet-500/20 text-violet-300 font-bold border border-violet-500/30 flex items-center gap-1.5">
                    <Sparkles size={14} /> BƯỚC 7: TÁI XẾP HẠNG &amp; HẠN NGẠCH KHỐI CHA
                  </span>
                  <h3 className="text-2xl font-black text-white">BGE-Reranker-v2-m3 &amp; SOTA Parent-Aware Quota</h3>
                </div>
                <span className="text-xs font-mono text-violet-300 font-bold bg-violet-950/60 px-3 py-1 rounded-xl border border-violet-500/30">
                  Cross-Encoder &bull; Quota 2-8 Khối Cha
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Chấm Điểm Tương Đồng Chéo Từng Cặp</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Khác với Bi-Encoder tính khoảng cách độc lập, Cross-Encoder <strong>BAAI/bge-reranker-v2-m3</strong> cho phép các token của câu hỏi con và văn bản tương tác qua ma trận Full Self-Attention, mang lại độ chính xác vượt bậc.
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-violet-400 font-bold mb-1">1. Lọc Ngưỡng An Toàn (0.20):</div>
                        <div className="text-[11px] text-slate-400">Loại bỏ ngay các đoạn văn rác không liên quan ngữ cảnh.</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-emerald-400 font-bold mb-1">2. Điểm Tốt Cốt Lõi (&ge; 0.65):</div>
                        <div className="text-[11px] text-slate-400">Được ưu tiên tối đa trong danh sách chọn nạp vào prompt.</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-violet-950/30 border border-violet-500/30 rounded-2xl text-xs font-mono text-violet-300">
                    &bull; Gom nhóm theo <code>parent_id</code>, không để các khối con cùng một cha chiếm hết slot của điều khoản khác!
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Bảng Phân Bổ Hạn Ngạch Động (Dynamic Quota)</h4>
                    
                    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-4 font-mono text-xs space-y-2.5">
                      <div className="grid grid-cols-3 gap-2 font-bold text-slate-400 pb-2 border-b border-slate-800 text-[11px]">
                        <div>SỐ SUB-QUERIES</div>
                        <div>HẠN NGẠCH / TRUY VẤN</div>
                        <div>TRẦN TỔNG SỐ KHỐI CHA</div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-slate-300 items-center">
                        <div className="font-bold text-cyan-300">1 Truy vấn đơn</div>
                        <div>Tối thiểu 3 khối cha</div>
                        <div className="text-emerald-400 font-bold">Tối đa 5 khối cha</div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-slate-300 items-center">
                        <div className="font-bold text-cyan-300">2 Truy vấn kép</div>
                        <div>2 đến 3 khối cha / query</div>
                        <div className="text-emerald-400 font-bold">Tối đa 5 khối cha</div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-slate-300 items-center">
                        <div className="font-bold text-cyan-300">3 Truy vấn kép</div>
                        <div>2 đến 3 khối cha / query</div>
                        <div className="text-emerald-400 font-bold">Tối đa 8 khối cha</div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-slate-300 items-center">
                        <div className="font-bold text-cyan-300">4 Truy vấn kép</div>
                        <div>2 khối cha / query</div>
                        <div className="text-emerald-400 font-bold">Tối đa 8 khối cha</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-violet-950/30 border border-violet-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-violet-300">
                    <span>Đảm bảo công bằng nội dung giữa các vế câu hỏi phức tạp</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 8: SMALL-TO-BIG & SANDWICH REORDER */}
          {activeStep === 8 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-fuchsia-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-fuchsia-500/20 text-fuchsia-300 font-bold border border-fuchsia-500/30 flex items-center gap-1.5">
                    <Maximize2 size={14} /> BƯỚC 8: BUNG NỞ &amp; HOÁN VỊ BÁNH KẸP
                  </span>
                  <h3 className="text-2xl font-black text-white">Small-to-Big Expansion &amp; Stanford Sandwich Reordering</h3>
                </div>
                <span className="text-xs font-mono text-fuchsia-300 font-bold bg-fuchsia-950/60 px-3 py-1 rounded-xl border border-fuchsia-500/30">
                  Lost-in-the-Middle Mitigation
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Cơ Chế Bung Nở Khối Cha (Small-to-Big)</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Khối con nhỏ gọn 600 ký tự giúp định vị chính xác điểm chạm ngữ nghĩa. Sau khi chọn lọc, hệ thống tự động thay thế bằng nội dung <strong>khối cha hoàn chỉnh 1.200 token</strong> (Parent Content) để mô hình nắm trọn vẹn văn cảnh của điều khoản.
                    </p>

                    <div className="bg-slate-900/90 p-3 rounded-2xl border border-slate-800">
                      <Img
                        src={staticFile('images/lost-in-the-middle-U-shaped performance curve.png')}
                        className="w-full h-36 object-contain rounded-xl"
                      />
                      <div className="text-[10px] text-center text-slate-400 mt-1.5 font-mono">
                        Nghiên cứu Stanford (Liu et al.): Chú ý cao ở 2 đầu, rơi tự do ở giữa prompt.
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-fuchsia-950/30 border border-fuchsia-500/30 rounded-2xl text-xs font-mono text-fuchsia-300">
                    &bull; Đưa 2 tài liệu tốt nhất vào 2 đỉnh chữ U (Primacy &amp; Recency).
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Giải Thuật Hoán Vị `_sandwich_reorder`</h4>
                    
                    <div className="bg-slate-900/95 rounded-2xl border border-slate-800 p-4 font-mono text-xs space-y-3">
                      <div className="flex items-center justify-between text-slate-300">
                        <span>Thứ tự từ Reranker:</span>
                        <span className="text-slate-400">[#1, #2, #3, #4, #5]</span>
                      </div>
                      <div className="flex items-center justify-between text-fuchsia-300 font-bold pt-1 border-t border-slate-800">
                        <span>Sau hoán vị bánh kẹp:</span>
                        <span className="text-emerald-400 font-bold">[#1, #3, #5, ..., #4, #2]</span>
                      </div>

                      {/* Visual Blocks */}
                      <div className="grid grid-cols-5 gap-2 my-2 text-center font-bold">
                        <div className="p-2.5 bg-emerald-500/25 border-2 border-emerald-400 text-emerald-300 rounded-xl">
                          <div className="text-sm font-black">#1</div>
                          <div className="text-[10px] mt-0.5">Đầu Prompt</div>
                          <div className="text-[9px] text-emerald-400">Đỉnh Primacy</div>
                        </div>
                        <div className="p-2.5 bg-slate-800 border border-slate-700 text-slate-400 rounded-xl">
                          <div className="text-sm font-black">#3</div>
                          <div className="text-[10px] mt-0.5">Bổ trợ</div>
                        </div>
                        <div className="p-2.5 bg-slate-800 border border-slate-700 text-slate-400 rounded-xl">
                          <div className="text-sm font-black">#5</div>
                          <div className="text-[10px] mt-0.5">Bổ trợ</div>
                        </div>
                        <div className="p-2.5 bg-slate-800 border border-slate-700 text-slate-400 rounded-xl">
                          <div className="text-sm font-black">#4</div>
                          <div className="text-[10px] mt-0.5">Bổ trợ</div>
                        </div>
                        <div className="p-2.5 bg-blue-500/25 border-2 border-blue-400 text-blue-300 rounded-xl">
                          <div className="text-sm font-black">#2</div>
                          <div className="text-[10px] mt-0.5">Sát Đáy Prompt</div>
                          <div className="text-[9px] text-blue-400">Đỉnh Recency</div>
                        </div>
                      </div>

                      <div className="text-[11px] text-slate-300 leading-relaxed pt-1">
                        Tài liệu #2 nằm sát thẻ <code>&lt;query_reminder&gt;</code> ở đáy prompt để nhận trọng số chú ý cực đại, loại bỏ hiện tượng đãng trí!
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-fuchsia-950/30 border border-fuchsia-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-fuchsia-300">
                    <span>Hiệu suất nhận thức của LLM đối với tài liệu #2 tăng hơn 35%</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 9: XML SANDBOX & DYNAMIC SYSTEM INSTRUCTION */}
          {activeStep === 9 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-orange-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-orange-500/20 text-orange-300 font-bold border border-orange-500/30 flex items-center gap-1.5">
                    <FileCode size={14} /> BƯỚC 9: ĐÓNG HỘP XML &amp; CHỈ THỊ HỆ THỐNG ĐỘNG
                  </span>
                  <h3 className="text-2xl font-black text-white">XML Sandboxing &amp; SpatioRoute: -60% Prompt Tokens</h3>
                </div>
                <span className="text-xs font-mono text-orange-300 font-bold bg-orange-950/60 px-3 py-1 rounded-xl border border-orange-500/30">
                  Arithmetic CoT &bull; CF-RAG
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Vùng An Toàn XML Sandboxing</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      Ngữ cảnh trích xuất được đóng gói chuẩn mực trong thẻ <code>&lt;retrieved_context&gt;</code>, phân lập tuyệt đối giữa dữ liệu tra cứu và chỉ thị điều khiển:
                    </p>

                    <div className="bg-slate-900/95 p-3.5 rounded-2xl border border-slate-800 font-mono text-xs space-y-1.5 text-slate-300 leading-relaxed">
                      <div className="text-orange-400 font-bold">&lt;retrieved_context&gt;</div>
                      <div className="pl-3 text-slate-400">&lt;source id="1"&gt; Nguồn: Quy chế Đào tạo 2024 ... &lt;/source&gt;</div>
                      <div className="pl-3 text-slate-400">&lt;source id="2"&gt; Nguồn: Cẩm nang Sinh viên K19 ... &lt;/source&gt;</div>
                      <div className="text-orange-400 font-bold">&lt;/retrieved_context&gt;</div>
                      
                      <div className="text-amber-300 pt-1.5 border-t border-slate-800 text-xs">
                        &lt;query_reminder&gt;<br />
                        &nbsp;&nbsp;Câu hỏi: Bị cảnh báo lần 1 đăng ký tối đa mấy tín chỉ?<br />
                        &lt;/query_reminder&gt;
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300">Kích thước prompt:</span>
                    <span className="text-emerald-400 font-bold">2.800 &rarr; 850 tokens (Tiết kiệm 60%)</span>
                  </div>
                </div>

                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Arithmetic CoT &amp; Thứ Tự Xung Đột CF-RAG</h4>
                    
                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800">
                        <div className="text-emerald-400 font-bold flex items-center gap-1.5 mb-1">
                          <Calculator size={14} /> Arithmetic CoT (Tính Số Học Từng Bước):
                        </div>
                        <div className="text-[11px] text-slate-300 bg-slate-950 p-2 rounded-lg">
                          <code>12 (đã đăng ký) + 4 (môn mới) = 16 &gt; 14 tín hạn mức &rArr; KHÔNG ĐƯỢC PHÉP</code>
                        </div>
                      </div>

                      <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800">
                        <div className="text-amber-400 font-bold flex items-center gap-1.5 mb-1">
                          <Scale size={14} /> Thứ Tự Giải Quyết Xung Đột CF-RAG:
                        </div>
                        <div className="text-[10px] text-slate-300 space-y-0.5">
                          <div>1. Ưu tiên Khóa tuyển sinh: Sinh viên K19 áp dụng Cẩm nang K19.</div>
                          <div>2. Ưu tiên Năm ban hành: Quyết định 2024 thay thế văn bản 2022.</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-orange-950/30 border border-orange-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-orange-300">
                    <span>Đảm bảo câu trả lời nhị phân dứt khoát: ĐƯỢC PHÉP hay KHÔNG ĐƯỢC PHÉP</span>
                    <FileCheck size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 10: LLM STREAM GENERATION */}
          {activeStep === 10 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-teal-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-teal-500/20 text-teal-300 font-bold border border-teal-500/30 flex items-center gap-1.5">
                    <Radio size={14} /> BƯỚC 10: SINH TRẢ LỜI &amp; STREAM SSE
                  </span>
                  <h3 className="text-2xl font-black text-white">Streaming Server-Sent Events &amp; Lọc Thẻ Suy Nghĩ Thời Gian Thực</h3>
                </div>
                <span className="text-xs font-mono text-teal-300 font-bold bg-teal-950/60 px-3 py-1 rounded-xl border border-teal-500/30">
                  Shared Model: Qwen3.6-35B-A3B-AWQ
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Gửi Trích Dẫn Citations Trước, Stream Text Sau</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Trước khi xuất dòng chữ đầu tiên, dịch vụ gửi gói tin metadata chứa danh sách các nguồn trích dẫn học vụ để giao diện hiển thị ngay cho sinh viên:
                    </p>

                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-teal-400 font-bold">1. Metadata SSE Packet:</div>
                        <div className="text-[11px] text-slate-300 mt-1">
                          <code>event: metadata<br />data: {`{"citations": [{"title": "Quy chế Đào tạo 2024", "section": "Điều 15"}]}`}</code>
                        </div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-cyan-400 font-bold">2. Delta Text SSE Packet:</div>
                        <div className="text-[11px] text-slate-300 mt-1">
                          <code>event: delta<br />data: {`{"text": "Theo Điều 15 Quy chế Đào tạo..."}`}</code>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-[11px] font-mono text-teal-300">
                    &bull; Giao thức SSE giúp độ trễ nhận ký tự đầu tiên (TTFT) chỉ còn <strong>650ms</strong>.
                  </div>
                </div>

                <div className="col-span-6 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Bộ Lọc Thẻ Suy Nghĩ Trực Tiếp Trên Server</h4>
                    <div className="bg-slate-900/95 rounded-2xl border border-slate-800 p-4 font-mono text-xs text-slate-200 space-y-2 leading-relaxed">
                      <div className="text-slate-500"># Bóc tách thẻ &lt;thinking&gt; trong luồng stream (llm_generation_service):</div>
                      <div className="text-rose-400 font-bold">Trong Mô Hình LLM Sinh Ra:</div>
                      <div className="p-2 bg-slate-950 rounded text-[11px] text-slate-400">
                        &lt;thinking&gt;<br />
                        &nbsp;&nbsp;&lt;doc_relevance&gt;YES&lt;/doc_relevance&gt;<br />
                        &nbsp;&nbsp;&lt;answer_confidence&gt;HIGH&lt;/answer_confidence&gt;<br />
                        &lt;/thinking&gt;<br />
                        Chào bạn, sinh viên bị cảnh báo học vụ lần 1...
                      </div>

                      <div className="text-emerald-400 font-bold pt-1">Đẩy Về Trình Duyệt Sinh Viên:</div>
                      <div className="p-2 bg-emerald-950/40 border border-emerald-500/40 rounded text-[11px] text-emerald-200">
                        "Chào bạn, sinh viên bị cảnh báo học vụ lần 1..."
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-teal-950/30 border border-teal-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-teal-300">
                    <span>Sinh viên chỉ nhận câu trả lời trau chuốt, suy nghĩ nội tâm được bảo mật tuyệt đối</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STEP 11: SELF-RAG QUALITY GATE & WRITE-BACK */}
          {activeStep === 11 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full bg-slate-900/95 border-2 border-green-500/50 rounded-3xl p-7 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono px-3 py-1 rounded bg-green-500/20 text-green-300 font-bold border border-green-500/30 flex items-center gap-1.5">
                    <CheckCircle2 size={14} /> BƯỚC 11: CHỐT CHẶN SELF-RAG &amp; GHI ĐỆM
                  </span>
                  <h3 className="text-2xl font-black text-white">Quality Gate &amp; Asynchronous Write-Back</h3>
                </div>
                <span className="text-xs font-mono text-green-300 font-bold bg-green-950/60 px-3 py-1 rounded-xl border border-green-500/30">
                  Chống Đầu Độc Cache &bull; TTL 24h / 7 Ngày
                </span>
              </div>

              <div className="grid grid-cols-12 gap-8 items-stretch">
                <div className="col-span-5 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">3 Điều Kiện Khắt Khe Để Ghi Cache</h4>
                    <p className="text-xs text-slate-300 leading-relaxed mb-4">
                      Hàm <code>async_cache_writeback()</code> chạy nền bất đồng bộ, chỉ cho phép câu trả lời được ghi vào bộ đệm khi vượt qua toàn bộ 3 chốt chặn:
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-emerald-400 font-bold mb-1">1. Điểm Tài Liệu: top_doc_score &gt;= 0.25</div>
                        <div className="text-[11px] text-slate-400">Ngăn chặn các câu hỏi thiếu ngữ cảnh tra cứu.</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-cyan-400 font-bold mb-1">2. Độ Dài: 10 &lt;= len(answer) &lt;= 3.000</div>
                        <div className="text-[11px] text-slate-400">Loại bỏ câu trả lời cụt lủn hoặc bị lỗi cắt ngắn.</div>
                      </div>

                      <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                        <div className="text-amber-400 font-bold mb-1">3. Thẻ Đánh Giá Tự Thân Self-RAG:</div>
                        <div className="text-[11px] text-slate-400">
                          &bull; <code>&lt;doc_relevance&gt; != NO</code><br />
                          &bull; <code>&lt;answer_confidence&gt; == HIGH</code>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-green-950/30 border border-green-500/30 rounded-2xl text-xs font-mono text-green-300">
                    &bull; Chống hoàn toàn hiện tượng ảo giác AI bị lưu đệm gây ảnh hưởng người hỏi sau!
                  </div>
                </div>

                <div className="col-span-7 bg-slate-950 p-5 rounded-3xl border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Ghi Đệm Song Song &amp; Nhật Ký Kiểm Toán</h4>
                    <div className="bg-slate-900/95 rounded-2xl border border-slate-800 p-4 font-mono text-xs text-slate-200 space-y-2.5 leading-relaxed">
                      <div className="text-slate-500"># Khi vượt qua Quality Gate:</div>
                      <div>
                        1. <strong className="text-emerald-300">Ghi Redis:</strong> key: <code>semantic_cache:&lt;query&gt;</code> &bull; TTL: <span className="text-amber-300 font-bold">24 Giờ</span> (86.400s)
                      </div>
                      <div>
                        2. <strong className="text-cyan-300">Ghi Supabase:</strong> bảng <code>semantic_cache</code> &bull; TTL: <span className="text-amber-300 font-bold">7 Ngày</span> (Lưu kèm vector 768d)
                      </div>
                      <div>
                        3. <strong className="text-purple-300">Lưu Lịch Sử:</strong> <code>save_turn_to_db()</code> lưu lượt hội thoại của sinh viên
                      </div>
                      <div>
                        4. <strong className="text-rose-300">Kiểm Toán:</strong> <code>write_full_rag_log_to_md()</code> ghi log chi tiết phục vụ nghiệm thu
                      </div>
                    </div>

                    <div className="mt-3 p-3 bg-slate-900 rounded-2xl border border-slate-800 text-xs font-mono text-slate-300">
                      Chu trình khép lại hoàn chỉnh: Một câu hỏi chỉ tốn tài nguyên tính toán 1 lần duy nhất; mọi sinh viên hỏi tương tự sau đó đều nhận phản hồi tức thì trong <strong>12ms</strong>!
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-green-950/30 border border-green-500/30 rounded-2xl flex items-center justify-between text-xs font-mono text-green-300">
                    <span>Hệ thống đạt tiêu chuẩn sẵn sàng vận hành thực tế tại IUH</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

        </div>

        {/* 4. Footer Progress Bar */}
        <div className="w-full flex items-center justify-between pt-2 border-t border-slate-800/80 font-mono text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>Đang phát: Bước {activeStep} / 11 &bull; {currentStepData.title}</span>
          </div>

          <div className="flex items-center gap-3">
            <span>Khung hình: {frame} / {timingsData.total_frames}</span>
            <div className="w-48 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500"
                style={{ width: `${(frame / timingsData.total_frames) * 100}%` }}
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
