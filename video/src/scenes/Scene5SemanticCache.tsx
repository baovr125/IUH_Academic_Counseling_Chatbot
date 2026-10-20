import React from 'react';
import { Audio, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Zap, Database, ShieldAlert, Cpu, CheckCircle2, Lock, Sparkles, AlertOctagon, Scale, Hash, Server } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';

export const Scene5SemanticCache: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Active section calibrated to sentenceTimings.json (Total 1724 frames ~ 57.47s):
  // Sentence 0 (frames 0 - 268): Overview & Peak Season Traffic
  // Sentence 1 (frames 276 - 488): Lớp 0 - Redis In-Memory O(1) 12ms
  // Sentence 2 (frames 496 - 768): Lớp 1 - pgvector Cosine 768d (ngưỡng 0.60)
  // Sentence 3 (frames 776 - 962): Lớp 2 - Cross-Encoder BGE-Reranker (ngưỡng 0.80)
  // Sentence 4 (frames 971 - 1366): Lớp Giáp - Entity Numbers Guard (chống nhầm năm học)
  // Sentence 5 (frames 1374 - 1715): Chốt Chặn - Self-RAG Gated Write-back
  let activeItem = 0;
  if (frame >= 272 && frame < 492) activeItem = 1;
  else if (frame >= 492 && frame < 772) activeItem = 2;
  else if (frame >= 772 && frame < 967) activeItem = 3;
  else if (frame >= 967 && frame < 1370) activeItem = 4;
  else if (frame >= 1370) activeItem = 5;

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene5.mp3')} volume={1} />
      <AnimatedBackground theme="amber" />

      <SceneMotionWrapper durationInFrames={1724} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        {/* Compact Integrated Header Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/25">
              <Zap size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-amber-400">
                  TWO-STAGE SEMANTIC CACHE &amp; ENTITY GUARD
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; REDIS O(1) + PGVECTOR + CROSS-ENCODER</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                TỐC ĐỘ &amp; AN TOÀN: BỘ NHỚ ĐỆM NGỮ NGHĨA 2 GIAI ĐOẠN
              </h1>
            </div>
          </div>

          {/* Carousel Stage Badges */}
          <div className="flex items-center gap-2">
            {[
              { num: 0, label: 'Tổng quan (2-Stage Cache)' },
              { num: 1, label: 'Lớp 0: Redis O(1)' },
              { num: 2, label: 'Lớp 1: pgvector 768d' },
              { num: 3, label: 'Lớp 2: Cross-Encoder 0.80' },
              { num: 4, label: 'Lớp Giáp: Entity Guard' },
              { num: 5, label: 'Chốt Chặn: Self-RAG Gate' }
            ].map((s) => (
              <span
                key={s.num}
                className={`text-xs font-mono font-bold px-3 py-1.5 rounded-xl border transition-colors ${
                  activeItem === s.num
                    ? 'bg-amber-600 text-white border-amber-400 shadow-lg shadow-amber-500/30'
                    : 'bg-slate-900/80 text-slate-400 border-slate-800'
                }`}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {/* Latency Benchmark Bar */}
        <div className="w-full max-w-[1780px] mx-auto bg-slate-900/95 border-2 border-slate-800 rounded-2xl px-6 py-2 shadow-xl font-mono text-xs flex items-center justify-between my-1">
          <div className="flex items-center gap-2 text-slate-300">
            <Zap size={16} className="text-amber-400" />
            <span>Hiệu năng đo lường thực tế (Production Metrics):</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-slate-300">Redis Cache Hit: <strong className="text-emerald-400 text-sm">12ms</strong> (O(1))</span>
            <span className="text-slate-300">Semantic pgvector Hit: <strong className="text-cyan-400 text-sm">&lt; 35ms</strong></span>
            <span className="text-slate-300">RAG Cold Query: <strong className="text-purple-400">0.8s - 1.2s</strong></span>
            <span className="text-slate-300">Tiết kiệm chi phí token: <strong className="text-amber-400">-60% Cost</strong></span>
          </div>
        </div>

        {/* Main Single-Focus Stage Area (Occupies ~75% screen) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full">
          
          {/* STAGE 0: OVERVIEW OF 2-STAGE CACHE (frames 0 - 272) */}
          {activeItem === 0 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-amber-500/50 rounded-3xl p-8 shadow-2xl flex flex-col items-center">
              <div className="text-center mb-6">
                <span className="text-xs font-mono px-3.5 py-1.5 rounded-full bg-amber-500/15 text-amber-400 font-bold border border-amber-500/30">
                  GIẢI PHÁP TĂNG TỐC VÀ BẢO VỆ TẢI HỌC KỲ
                </span>
                <h3 className="text-3xl font-black text-white mt-2">
                  Phục Vụ Hàng Nghìn Sinh Viên Trong Mùa Cao Điểm
                </h3>
                <p className="text-sm text-slate-300 mt-1">
                  Đón đầu các câu hỏi học phí, điểm chuẩn và lịch thi có tần suất lặp lại cao với cơ chế kiểm chứng đa tầng không ảo giác.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-6 w-full max-w-[1500px]">
                <div className="bg-slate-950 p-6 rounded-2xl border border-red-500/40 text-center">
                  <div className="w-12 h-12 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center font-bold mx-auto mb-3">
                    <Server size={24} />
                  </div>
                  <h4 className="text-base font-bold text-white">Lớp 0: Redis Cache</h4>
                  <p className="text-xs text-slate-400 mt-1 font-mono">In-Memory Hash O(1)</p>
                  <div className="mt-3 text-2xl font-black font-mono text-emerald-400">12ms</div>
                  <span className="text-[11px] text-slate-400 block mt-1">Phản hồi gần như tức thì</span>
                </div>

                <div className="bg-slate-950 p-6 rounded-2xl border border-cyan-500/40 text-center">
                  <div className="w-12 h-12 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold mx-auto mb-3">
                    <Database size={24} />
                  </div>
                  <h4 className="text-base font-bold text-white">Lớp 1: pgvector Cosine</h4>
                  <p className="text-xs text-slate-400 mt-1 font-mono">HNSW Vector 768d</p>
                  <div className="mt-3 text-2xl font-black font-mono text-cyan-400">&ge; 0.60</div>
                  <span className="text-[11px] text-slate-400 block mt-1">Bao quát câu hỏi đồng nghĩa</span>
                </div>

                <div className="bg-slate-950 p-6 rounded-2xl border border-amber-500/40 text-center">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold mx-auto mb-3">
                    <ShieldAlert size={24} />
                  </div>
                  <h4 className="text-base font-bold text-white">Lớp 2: Cross-Encoder + Entity</h4>
                  <p className="text-xs text-slate-400 mt-1 font-mono">BGE-Reranker &amp; Numbers</p>
                  <div className="mt-3 text-2xl font-black font-mono text-amber-400">&ge; 0.80</div>
                  <span className="text-[11px] text-slate-400 block mt-1">Triệt tiêu nhầm lẫn năm học</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 1: LỚP 0 - REDIS O(1) 12MS (frames 272 - 492) */}
          {activeItem === 1 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-red-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-red-500/20 text-red-300 font-bold border border-red-500/40 flex items-center gap-2">
                      <Zap size={16} /> LỚP 0: BỘ ĐỆM REDIS IN-MEMORY O(1)
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-500/30">
                      12ms Response
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Tra Cứu Khóa Ký Tự Chuẩn Hóa Độ Phức Tạp O(1)
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-red-400 block mb-1">Cơ chế hoạt động lớp 0:</strong>
                    Câu hỏi của sinh viên trước hết được chuẩn hóa (loại bỏ khoảng trắng thừa, đưa về chữ thường). Hệ thống băm thành khóa ký tự và kiểm tra trực tiếp trên cụm bộ nhớ RAM Redis với độ phức tạp O(1). Nếu trúng khóa (Cache Hit), câu trả lời đã được thẩm định trước đó được trả về chỉ trong 12 mili giây.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-red-950/30 border border-red-500/30 rounded-2xl text-xs font-mono text-red-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Data Structure:</span>
                      <strong className="text-emerald-400">Redis String / Hash O(1)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Cold RAG Pipeline:</span>
                      <strong className="text-emerald-400">BYPASSED ENTIRELY</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Server Load Reduction:</span>
                      <strong className="text-emerald-400">-80% Database IOPS</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
                    <span>Phản hồi tức thì trong mùa đăng ký học phần</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>

              {/* Redis Architecture Visual */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-red-400 font-bold flex items-center gap-1.5">
                    <Server size={16} /> Redis 7 In-Memory Key Lookup
                  </span>
                  <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-0.5 rounded border border-emerald-500/20 font-bold">
                    O(1) Hash Map
                  </span>
                </div>
                <div className="pt-4 space-y-3 text-slate-200 text-sm leading-relaxed overflow-x-auto">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1 text-xs">
                    <div className="text-slate-400 font-bold">// Key chuẩn hóa trong Redis:</div>
                    <div className="text-amber-300">"semantic_cache:exact:canh_bao_hoc_vu_lan_1"</div>
                    <div className="pt-2 text-slate-400 font-bold">// Payload lưu trữ:</div>
                    <div className="text-slate-300 leading-relaxed">
                      {'{ "answer": "Theo Điều 14 Sổ tay Sinh viên IUH 2024, sinh viên bị cảnh báo học vụ lần 1 chỉ được phép đăng ký tối đa 14 tín chỉ...", "source": "Điều 14", "verified": true }'}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between">
                    <span>Thời gian hoàn tất truy vấn:</span>
                    <strong className="text-emerald-400 text-sm">12ms (Round-trip)</strong>
                  </div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Tiết kiệm 100% tài nguyên tính toán và chi phí API</span>
                  <span className="text-emerald-400 font-bold">O(1) Latency</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 2: LỚP 1 - PGVECTOR COSINE 768D (frames 492 - 772) */}
          {activeItem === 2 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-cyan-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40 flex items-center gap-2">
                      <Database size={16} /> LỚP 1: PGVECTOR COSINE 768D (NGƯỠNG 0.60)
                    </span>
                    <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-lg border border-cyan-500/30">
                      Broad Semantic Filter
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Quét Nhanh Các Câu Hỏi Đồng Nghĩa
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-cyan-400 block mb-1">Cơ chế quét vector bao quát:</strong>
                    Nếu không khớp tuyệt đối ở Redis (ví dụ sinh viên dùng từ ngữ khác như "bị cảnh cáo học vụ" thay vì "cảnh báo học vụ"), truy vấn vector 768 chiều được gửi tới PostgreSQL pgvector. Với ngưỡng bao quát 0.60, hệ thống quét nhanh tất cả các câu hỏi có ngữ nghĩa tương đồng trong kho đệm.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl text-xs font-mono text-cyan-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Embedding Model:</span>
                      <strong className="text-emerald-400">vietnamese-bi-encoder (768d)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Cosine Distance Operator:</span>
                      <strong className="text-emerald-400">1 - (embedding &lt;=&gt; q_vector)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Recall Threshold:</span>
                      <strong className="text-cyan-400">&ge; 0.60 (Lấy top 5 ứng viên)</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-cyan-300 flex items-center justify-between">
                    <span>Không bỏ sót bất kỳ biến thể diễn đạt đồng nghĩa nào</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* SQL pgvector Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                    <Database size={16} /> PostgreSQL 16 pgvector SQL
                  </span>
                  <span className="bg-cyan-500/10 text-cyan-400 px-2.5 py-0.5 rounded border border-cyan-500/20 font-bold">
                    HNSW Cosine Search
                  </span>
                </div>
                <div className="pt-4 space-y-2 text-slate-200 text-sm leading-relaxed overflow-x-auto">
                  <div className="text-cyan-400 font-bold">SELECT</div>
                  <div className="pl-4">id, cached_query, cached_answer,</div>
                  <div className="pl-4 text-emerald-400">
                    1 - (embedding &lt;=&gt; $1::vector) AS cosine_sim
                  </div>
                  <div className="text-cyan-400 font-bold">FROM</div>
                  <div className="pl-4">semantic_cache_entries</div>
                  <div className="text-cyan-400 font-bold">WHERE</div>
                  <div className="pl-4 text-amber-300">
                    1 - (embedding &lt;=&gt; $1::vector) &gt;= <span className="text-cyan-300 font-bold">0.60</span>
                  </div>
                  <div className="text-cyan-400 font-bold">ORDER BY</div>
                  <div className="pl-4">cosine_sim DESC LIMIT 5;</div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Truy vấn chỉ mất dưới 25ms nhờ chỉ mục HNSW m=16</span>
                  <span className="text-emerald-400 font-bold">Execution: 24ms</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 3: LỚP 2 - CROSS-ENCODER 0.80 (frames 772 - 967) */}
          {activeItem === 3 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-indigo-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/40 flex items-center gap-2">
                      <Cpu size={16} /> LỚP 2: BGE-RERANKER CROSS-ENCODER (NGƯỠNG 0.80)
                    </span>
                    <span className="text-xs font-mono text-indigo-300 font-bold bg-indigo-950/60 px-3 py-1 rounded-lg border border-indigo-500/30">
                      Deep Cross-Attention
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Kiểm Định Tương Đồng Ngữ Nghĩa Sâu
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-indigo-400 block mb-1">Tại sao cần Cross-Encoder?</strong>
                    Mô hình Bi-Encoder ở Lớp 1 chỉ so sánh hai vector độc lập, dễ bị đánh lừa bởi những câu cùng từ vựng nhưng ngược nghĩa. Lớp 2 đưa cả cặp câu vào mô hình Cross-Encoder để từng từ tương tác chéo qua ma trận Attention, áp dụng ngưỡng kiểm duyệt khắt khe 0.80.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-indigo-950/30 border border-indigo-500/30 rounded-2xl text-xs font-mono text-indigo-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Interaction Mechanism:</span>
                      <strong className="text-emerald-400">All-to-All Cross Attention</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Strict Confidence Threshold:</span>
                      <strong className="text-emerald-400">&ge; 0.80 Score</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; False Semantic Match:</span>
                      <strong className="text-emerald-400">ELIMINATED COMPLETELY</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-indigo-300 flex items-center justify-between">
                    <span>Đảm bảo chỉ trả lời khi câu hỏi hoàn toàn trùng khớp về nghĩa</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Cross-Encoder Attention Matrix Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-indigo-400 font-bold flex items-center gap-1.5">
                    <Cpu size={16} /> BGE-Reranker-v2-m3 Cross Attention
                  </span>
                  <span className="bg-indigo-500/10 text-indigo-400 px-2.5 py-0.5 rounded border border-indigo-500/20 font-bold">
                    Threshold &ge; 0.80
                  </span>
                </div>
                <div className="pt-4 space-y-3 text-slate-200 text-sm leading-relaxed">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1 text-xs">
                    <div className="text-slate-400">Input Pair:</div>
                    <div><span className="text-purple-400">User Q</span>: "Cảnh cáo học vụ lần 1 đăng ký tối đa mấy chỉ?"</div>
                    <div><span className="text-cyan-400">Cache Q</span>: "Cảnh báo học vụ lần 1 học kỳ tới đăng ký tối đa bao nhiêu tín chỉ?"</div>
                  </div>
                  <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/40 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span>Điểm tương tác Cross-Encoder:</span>
                      <strong className="text-emerald-400 text-base">0.924 (&ge; 0.80)</strong>
                    </div>
                    <div className="text-emerald-400 font-bold">
                      ✓ Đạt chuẩn tương đồng ngữ nghĩa sâu &rarr; Tiếp tục qua Lớp Giáp Thực Thể.
                    </div>
                  </div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Chấm điểm tương tác chéo sâu loại bỏ hoàn toàn các câu hỏi lệch nghĩa</span>
                  <span className="text-emerald-400 font-bold">Score: 0.924</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 4: LỚP GIÁP - ENTITY NUMBERS GUARD (frames 967 - 1370) */}
          {activeItem === 4 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-amber-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40 flex items-center gap-2">
                      <Hash size={16} /> LỚP GIÁP: ENTITY NUMBERS GUARD
                    </span>
                    <span className="text-xs font-mono text-rose-400 font-bold bg-rose-950/60 px-3 py-1 rounded-lg border border-rose-500/30">
                      Chống Nhầm Năm Học
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    So Khớp Tuyệt Đối Từng Con Số Thực Thể
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-amber-400 block mb-1">Tử huyệt của Vector Embedding:</strong>
                    Hai câu hỏi "Học phí K19 năm 2024" và "Học phí K19 năm 2025" có độ tương đồng vector lên tới 0.98! Nếu chỉ dùng vector, hệ thống sẽ trả nhầm mức học phí năm cũ cho sinh viên năm mới. Lớp giáp Entity Numbers Guard trích xuất và đối soát từng con số thực thể: năm học, học kỳ, mức điểm GPA.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-amber-950/30 border border-amber-500/30 rounded-2xl text-xs font-mono text-amber-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Numerical Entity Extraction:</span>
                      <strong className="text-emerald-400">Regex Tokenizer Pattern</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Set Intersection Match:</span>
                      <strong className="text-emerald-400">set(Q_numbers) == set(Cache_numbers)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; 2024 vs 2025 Mismatch:</span>
                      <strong className="text-rose-400 font-bold">IMMEDIATELY REJECTED</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-amber-300 flex items-center justify-between">
                    <span>Ngăn chặn hoàn toàn việc nhầm lẫn giữa năm 2024 và 2025</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Case Demo: Rejected vs Passed */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl space-y-4">
                {/* Blocked Case */}
                <div className="p-3 rounded-2xl bg-rose-950/20 border border-rose-500/40">
                  <div className="text-rose-400 font-bold flex items-center justify-between mb-2">
                    <span>&times; Ca Bị Chặn: Lệch số năm học dù Vector tương đồng 0.98</span>
                    <span className="text-[10px] bg-rose-500/20 px-2 py-0.5 rounded text-rose-300">BÁC BỎ CACHE</span>
                  </div>
                  <div className="space-y-1 text-slate-300 text-xs">
                    <div>User Query: <span className="text-cyan-300">"Học phí tín chỉ K19 năm <strong className="text-amber-400 underline">2025</strong>"</span> &rarr; Số: [19, 2025]</div>
                    <div>Cache Query: <span className="text-slate-400">"Học phí tín chỉ K19 năm <strong className="text-rose-400 underline">2024</strong>"</span> &rarr; Số: [19, 2024]</div>
                    <div className="text-rose-400 font-bold pt-1 border-t border-slate-800">
                      &rarr; 2025 != 2024: Entity Guard từ chối trả Cache! Ép hệ thống chạy RAG mới.
                    </div>
                  </div>
                </div>

                {/* Passed Case */}
                <div className="p-3 rounded-2xl bg-emerald-950/30 border border-emerald-500/50">
                  <div className="text-emerald-400 font-bold flex items-center justify-between mb-2">
                    <span>✓ Ca Hợp Lệ: Trùng khớp chính xác con số thực thể</span>
                    <span className="text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-300">TRẢ CACHE 12MS</span>
                  </div>
                  <div className="space-y-1 text-slate-300 text-xs">
                    <div>User Query: <span className="text-cyan-300">"Cảnh báo học vụ lần <strong className="text-emerald-400 underline">1</strong> tối đa mấy tín chỉ?"</span> &rarr; Số: [1]</div>
                    <div>Cache Query: <span className="text-slate-400">"Cảnh báo học vụ lần <strong className="text-emerald-400 underline">1</strong> đăng ký bao nhiêu tín chỉ?"</span> &rarr; Số: [1]</div>
                    <div className="text-emerald-400 font-bold pt-1 border-t border-slate-800">
                      &rarr; Trùng số 1 + Cross-Encoder 0.92 &rarr; TRẢ KẾT QUẢ NGAY LẬP TỨC!
                    </div>
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 5: CHỐT CHẶN - SELF-RAG CACHE WRITE GATE (frames 1370 - 1724) */}
          {activeItem === 5 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-emerald-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40 flex items-center gap-2">
                      <Lock size={16} /> CHỐT CHẶN: SELF-RAG CACHE WRITE GATE
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-500/30">
                      Chống Đầu Độc Cache 100%
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Kiểm Soát Ghi Đệm Bằng Thẻ Tự Đánh Giá Self-RAG
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-emerald-400 block mb-1">Cơ chế chống đầu độc cache (Anti-Cache Poisoning):</strong>
                    Nếu câu trả lời sinh ra bị ảo giác hoặc trích xuất sai văn bản mà lưu vào cache, mọi sinh viên sau đó sẽ đều nhận thông tin sai lệch. Cơ chế Self-RAG phân tích thẻ phản xạ trong khối suy nghĩ: chỉ khi <code>&lt;doc_relevance&gt;</code> khác NO và <code>&lt;answer_confidence&gt;</code> là HIGH thì mới cho phép ghi vào Redis.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl text-xs font-mono text-emerald-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Document Relevance Check:</span>
                      <strong className="text-emerald-400">&lt;doc_relevance&gt; != NO</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Answer Confidence Check:</span>
                      <strong className="text-emerald-400">&lt;answer_confidence&gt; == HIGH</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Asynchronous Write-back:</span>
                      <strong className="text-emerald-400">Non-blocking Celery Task</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
                    <span>Bảo vệ độ tin cậy tuyệt đối cho toàn bộ cơ sở tri thức đệm</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>

              {/* Reflection Flow Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                    <Sparkles size={16} /> Self-RAG Reflection Gated Write-back
                  </span>
                  <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-0.5 rounded border border-emerald-500/20 font-bold">
                    Quality Gate
                  </span>
                </div>
                <div className="pt-4 space-y-3 text-slate-200 text-sm leading-relaxed overflow-x-auto">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1 text-xs">
                    <div className="text-slate-400 font-bold">// Khối suy nghĩ mô hình sinh ra:</div>
                    <div className="text-slate-300">
                      &lt;thinking&gt;<br />
                      &nbsp;&nbsp;<span className="text-emerald-400">&lt;doc_relevance&gt;YES&lt;/doc_relevance&gt;</span><br />
                      &nbsp;&nbsp;<span className="text-emerald-400">&lt;conflict_detected&gt;NO&lt;/conflict_detected&gt;</span><br />
                      &nbsp;&nbsp;<span className="text-emerald-400">&lt;answer_confidence&gt;HIGH&lt;/answer_confidence&gt;</span><br />
                      &lt;/thinking&gt;
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-xs text-emerald-200 space-y-1">
                    <div className="font-bold text-emerald-400">✓ Điều Kiện Ghi Đệm Thỏa Mãn:</div>
                    <div>&bull; Lưu Redis: khóa băm chuỗi chuẩn hóa (TTL: 7 ngày)</div>
                    <div>&bull; Lưu pgvector: vector 768d cho các truy vấn tương tự tiếp theo</div>
                  </div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Chặn đứng 100% nguy cơ lưu câu trả lời ảo giác vào bộ đệm</span>
                  <span className="text-emerald-400 font-bold">100% Anti-Poisoned</span>
                </div>
              </div>
            </FloatingCard>
          )}

        </div>

      </SceneMotionWrapper>
    </div>
  );
};
