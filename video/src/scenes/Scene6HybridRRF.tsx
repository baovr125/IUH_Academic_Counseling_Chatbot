import React from 'react';
import { Audio, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { GitMerge, Database, Search, Cpu, CheckCircle2, Filter, Layers, Calculator, Sparkles, Scale, Maximize2 } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';

export const Scene6HybridRRF: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Active section calibrated to sentenceTimings.json (Total 1690 frames ~ 56.34s):
  // Sentence 0 (frames 0 - 142): Overview of 3-step hybrid retrieval
  // Sentence 1 (frames 150 - 546): Bước 1 - Phân loại 7 ý định & Phân rã câu hỏi kép
  // Sentence 2 (frames 555 - 904): Bước 2 - Tìm kiếm song song HNSW & BM25 qua RRF (k=60)
  // Sentence 3 (frames 913 - 1188): Toán học RRF - Đồng thuận 0.0322 > 0.0163
  // Sentence 4 (frames 1197 - 1415): Bước 3 - BGE-Reranker & Quota 2-8 khối cha
  // Sentence 5 (frames 1424 - 1681): Cơ chế Small-to-Big bung 1.200 token
  let activeItem = 0;
  if (frame >= 146 && frame < 550) activeItem = 1;
  else if (frame >= 550 && frame < 909) activeItem = 2;
  else if (frame >= 909 && frame < 1193) activeItem = 3;
  else if (frame >= 1193 && frame < 1420) activeItem = 4;
  else if (frame >= 1420) activeItem = 5;

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene6.mp3')} volume={1} />
      <AnimatedBackground theme="blue" />

      <SceneMotionWrapper durationInFrames={1690} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        {/* Compact Integrated Header Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <GitMerge size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-blue-400">
                  HYBRID RETRIEVAL &amp; RECIPROCAL RANK FUSION
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; DENSE HNSW + SPARSE BM25 &bull; RRF (K=60)</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                TRUY XUẤT LAI HỢP: HYBRID RRF &amp; SMALL-TO-BIG EXPANSION
              </h1>
            </div>
          </div>

          {/* Carousel Stage Badges */}
          <div className="flex items-center gap-2">
            {[
              { num: 0, label: 'Tổng quan (3 Bước)' },
              { num: 1, label: 'Bước 1: 7 Ý định & Phân rã' },
              { num: 2, label: 'Bước 2: Song song & RRF' },
              { num: 3, label: 'Toán học: Đồng thuận RRF' },
              { num: 4, label: 'Bước 3: Reranker & Quota' },
              { num: 5, label: 'Bung nở: Small-to-Big' }
            ].map((s) => (
              <span
                key={s.num}
                className={`text-xs font-mono font-bold px-3 py-1.5 rounded-xl border transition-colors ${
                  activeItem === s.num
                    ? 'bg-blue-600 text-white border-blue-400 shadow-lg shadow-blue-500/30'
                    : 'bg-slate-900/80 text-slate-400 border-slate-800'
                }`}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {/* Pipeline Formula Bar */}
        <div className="w-full max-w-[1780px] mx-auto bg-slate-900/95 border-2 border-slate-800 rounded-2xl px-6 py-2 shadow-xl font-mono text-xs flex items-center justify-between my-1">
          <div className="flex items-center gap-2 text-slate-300">
            <Calculator size={16} className="text-blue-400" />
            <span>Công thức dung hợp xếp hạng (RRF Formula):</span>
            <code className="text-cyan-300 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              Score(d) = &sum; [ 1 / (60 + rank_i(d)) ]
            </code>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-slate-300">Kênh Dense: <strong className="text-purple-400">Vector HNSW 768d</strong></span>
            <span className="text-slate-300">Kênh Sparse: <strong className="text-cyan-400">PostgreSQL BM25</strong></span>
            <span className="text-slate-300">Hằng số k: <strong className="text-emerald-400">60</strong></span>
            <span className="text-slate-300">Quota: <strong className="text-amber-400">2 - 8 Khối cha</strong></span>
          </div>
        </div>

        {/* Main Single-Focus Stage Area (Occupies ~75% screen) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full">
          
          {/* STAGE 0: OVERVIEW OF 3 RETRIEVAL STEPS (frames 0 - 146) */}
          {activeItem === 0 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-blue-500/50 rounded-3xl p-8 shadow-2xl flex flex-col items-center">
              <div className="text-center mb-6">
                <span className="text-xs font-mono px-3.5 py-1.5 rounded-full bg-blue-500/15 text-blue-400 font-bold border border-blue-500/30">
                  KHI BỘ ĐỆM CACHE KHÔNG TRÚNG (CACHE MISS)
                </span>
                <h3 className="text-3xl font-black text-white mt-2">
                  Quy Trình Truy Xuất Lai Hợp 3 Bước Độc Lập
                </h3>
                <p className="text-sm text-slate-300 mt-1">
                  Kết hợp sức mạnh hiểu ngữ nghĩa của Vector và độ chính xác tuyệt đối của từ khóa pháp lý trên cơ sở dữ liệu PostgreSQL.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-6 w-full max-w-[1500px]">
                <div className="bg-slate-950 p-6 rounded-2xl border border-cyan-500/40 text-center">
                  <div className="w-12 h-12 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold mx-auto mb-3">1</div>
                  <h4 className="text-base font-bold text-white">Bước 1: Tiền Truy Xuất</h4>
                  <p className="text-xs text-slate-400 mt-1 font-mono">Shared LLM Rewriter</p>
                  <p className="text-xs text-slate-300 mt-2">Phân loại 7 ý định &amp; rã câu hỏi kép thành tối đa 4 truy vấn con.</p>
                </div>

                <div className="bg-slate-950 p-6 rounded-2xl border border-blue-500/40 text-center">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold mx-auto mb-3">2</div>
                  <h4 className="text-base font-bold text-white">Bước 2: Tìm Kiếm Song Song</h4>
                  <p className="text-xs text-slate-400 mt-1 font-mono">HNSW Vector + BM25</p>
                  <p className="text-xs text-slate-300 mt-2">Truy vấn song song 2 kênh trên PostgreSQL và dung hợp bằng công thức RRF (k=60).</p>
                </div>

                <div className="bg-slate-950 p-6 rounded-2xl border border-purple-500/40 text-center">
                  <div className="w-12 h-12 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold mx-auto mb-3">3</div>
                  <h4 className="text-base font-bold text-white">Bước 3: Hậu Truy Xuất</h4>
                  <p className="text-xs text-slate-400 mt-1 font-mono">BGE-Reranker &amp; Small-to-Big</p>
                  <p className="text-xs text-slate-300 mt-2">Tái xếp hạng tương tác chéo, lọc hạn ngạch quota, bung khối cha 1.200 token.</p>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 1: BƯỚC 1 - 7 Ý ĐỊNH & PHÂN RÃ CÂU HỎI KÉP (frames 146 - 550) */}
          {activeItem === 1 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-cyan-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40 flex items-center gap-2">
                      <Search size={16} /> BƯỚC 1: 7 Ý ĐỊNH &amp; PHÂN RÃ TRUY VẤN
                    </span>
                    <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-lg border border-cyan-500/30">
                      Zero-Shot JSON Schema
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Phân Loại 7 Ý Định &amp; Rã Câu Hỏi Kép
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-cyan-400 block mb-1">Cơ chế xử lý thông minh:</strong>
                    Mô hình ngôn ngữ lớn phân loại câu hỏi vào một trong bảy nhóm ý định học vụ (Chung, Điểm số, Đăng ký môn, Học phí, Tốt nghiệp, Khiếu nại, Khủng hoảng). Nếu là câu chào hỏi xã giao, hệ thống bỏ qua truy xuất để tiết kiệm tài nguyên. Nếu là câu hỏi kép phức tạp, mô hình tự động phân rã thành tối đa 4 truy vấn con độc lập.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl text-xs font-mono text-cyan-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Greeting / Social Query:</span>
                      <strong className="text-amber-400">BYPASS RETRIEVAL (0 Token Search)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Compound Query Decomposition:</span>
                      <strong className="text-emerald-400">Lên tới 4 Sub-Queries</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Shared Backend Model:</span>
                      <strong className="text-emerald-400">Dùng Chung LLM Với Generator</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-cyan-300 flex items-center justify-between">
                    <span>Phản hồi dưới dạng JSON thuần túy, không cần PPO phức tạp</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* JSON Rewriter Demo Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                    <Cpu size={16} /> Rewriter Output JSON
                  </span>
                  <span className="bg-cyan-500/10 text-cyan-400 px-2.5 py-0.5 rounded border border-cyan-500/20 font-bold">
                    Zero-Shot JSON
                  </span>
                </div>
                <div className="pt-4 space-y-2 text-slate-200 text-sm leading-relaxed overflow-x-auto">
                  <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <span className="text-slate-400 block mb-1">User Query Gốc:</span>
                    <span className="text-amber-300 font-bold">"Học phí ngành CNTT K19 bao nhiêu và hạn đóng tiền học kỳ này khi nào?"</span>
                  </div>
                  <div className="pt-2 text-xs">
                    <div>{'{'}</div>
                    <div className="pl-4"><span className="text-purple-400">"intent"</span>: <span className="text-emerald-300">"TUITION_POLICY"</span>,</div>
                    <div className="pl-4"><span className="text-purple-400">"need_retrieval"</span>: <span className="text-emerald-400 font-bold">true</span>,</div>
                    <div className="pl-4"><span className="text-purple-400">"sub_queries"</span>: [</div>
                    <div className="pl-8 text-cyan-300">"Học phí tín chỉ ngành Công nghệ thông tin khóa 19",</div>
                    <div className="pl-8 text-indigo-300">"Thời hạn nộp học phí học kỳ hiện tại theo thông báo phòng tài chính"</div>
                    <div className="pl-4">]</div>
                    <div>{'}'}</div>
                  </div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Mỗi truy vấn con được gửi song song tới PostgreSQL</span>
                  <span className="text-emerald-400 font-bold">Latency: 120ms</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 2: BƯỚC 2 - TÌM KIẾM SONG SONG DENSE & SPARSE RRF (frames 550 - 909) */}
          {activeItem === 2 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-blue-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-blue-500/20 text-blue-300 font-bold border border-blue-500/40 flex items-center gap-2">
                      <GitMerge size={16} /> BƯỚC 2: TÌM KIẾM SONG SONG &amp; RRF (K=60)
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-500/30">
                      PostgreSQL 16 Engine
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Dung Hợp Vector HNSW &amp; Từ Khóa BM25
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-blue-400 block mb-1">Cơ chế thực thi trên cơ sở dữ liệu:</strong>
                    Mỗi truy vấn con thực thi tìm kiếm song song trên PostgreSQL: Kênh Dense sử dụng chỉ mục HNSW trên vector ngữ nghĩa 768 chiều để bắt trọn ý định câu hỏi; Kênh Sparse sử dụng Full-Text Search BM25 trên cột tsvector để bắt chính xác các thuật ngữ viết tắt và mã môn học. Kết quả hai kênh được dung hợp qua hàm RRF với hằng số chuẩn k=60.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-blue-950/30 border border-blue-500/30 rounded-2xl text-xs font-mono text-blue-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Dense Index:</span>
                      <strong className="text-emerald-400">pgvector HNSW Cosine (768d)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Sparse Index:</span>
                      <strong className="text-cyan-400">tsvector Full-Text Search simple</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Smoothing Constant:</span>
                      <strong className="text-emerald-400">k = 60 (Chuẩn quốc tế Cormack et al.)</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-blue-300 flex items-center justify-between">
                    <span>Không thiên vị điểm số của bất kỳ thuật toán đơn lẻ nào</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Parallel Flow Visualization */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-blue-400 font-bold flex items-center gap-1.5">
                    <Database size={16} /> PostgreSQL 16 Parallel Execution
                  </span>
                  <span className="bg-blue-500/10 text-blue-400 px-2.5 py-0.5 rounded border border-blue-500/20 font-bold">
                    Async Multi-Query
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-2xl bg-slate-900 border border-purple-500/40 space-y-1">
                    <span className="text-purple-400 font-bold block">1. Nhánh Dense Vector</span>
                    <div className="text-[11px] text-slate-300">&bull; vietnamese-bi-encoder</div>
                    <div className="text-[11px] text-slate-300">&bull; HNSW Cosine Similarity</div>
                    <div className="text-emerald-400 font-bold text-[10px] mt-1">Bắt câu hỏi diễn đạt khác từ</div>
                  </div>
                  <div className="p-3 rounded-2xl bg-slate-900 border border-cyan-500/40 space-y-1">
                    <span className="text-cyan-400 font-bold block">2. Nhánh Sparse Từ Khóa</span>
                    <div className="text-[11px] text-slate-300">&bull; to_tsvector('simple', text)</div>
                    <div className="text-[11px] text-slate-300">&bull; BM25 Term Matching</div>
                    <div className="text-cyan-400 font-bold text-[10px] mt-1">Bắt mã môn, từ viết tắt IUH</div>
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-blue-950/40 border border-blue-500/40 text-center space-y-1">
                  <div className="text-blue-300 font-bold text-xs">DUNG HỢP RECIPROCAL RANK FUSION (RRF)</div>
                  <code className="text-emerald-400 font-bold text-sm block">RRF = &sum; [ 1 / (60 + rank) ]</code>
                  <div className="text-[10px] text-slate-400">Tài liệu xuất hiện trên cả 2 danh sách được cộng dồn điểm số nghịch đảo</div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 3: TOÁN HỌC RRF - ĐỒNG THUẬN LUÔN THẮNG (frames 909 - 1193) */}
          {activeItem === 3 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-emerald-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40 flex items-center gap-2">
                      <Scale size={16} /> TOÁN HỌC RRF: ĐỒNG THUẬN ĐA NGUỒN
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-500/30">
                      Chứng Minh Toán Học
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    0.0322 Điểm Đồng Thuận Luôn Thắng Tuyệt Đối
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-emerald-400 block mb-1">Bản chất vượt trội của công thức:</strong>
                    Tài liệu A chỉ đứng thứ 2 ở cả hai danh sách Dense và Sparse sẽ nhận được số điểm <code>1/62 + 1/62 = 0.0322</code>. Trong khi đó, tài liệu B đứng đầu tuyệt đối (Rank 1) ở một kênh nhưng kênh kia hoàn toàn không tìm thấy sẽ chỉ nhận <code>1/61 = 0.0163</code>. Số điểm của tài liệu đồng thuận cao gần gấp đôi, chứng minh bằng toán học rằng sự đồng thuận đa thuật toán luôn chiến thắng sự phỏng đoán đơn độc.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl text-xs font-mono text-emerald-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Dual-channel Consensus Score:</span>
                      <strong className="text-emerald-400">0.0322 (Doc A)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Single-channel Rank 1 Score:</span>
                      <strong className="text-amber-400">0.0163 (Doc B)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Mathematical Margin:</span>
                      <strong className="text-emerald-400">+97.5% Score Advantage</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
                    <span>Triệt tiêu thiên vị của từng thuật toán tìm kiếm cục bộ</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>

              {/* Mathematical Comparison Table */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                    <Calculator size={16} /> Bảng So Sánh Điểm Số Thực Nghiệm
                  </span>
                  <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-0.5 rounded border border-emerald-500/20 font-bold">
                    k = 60
                  </span>
                </div>

                {/* Doc A: Consensus */}
                <div className="p-3.5 rounded-2xl bg-emerald-950/30 border border-emerald-500/50 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">Tài Liệu A (Đồng thuận 2 kênh)</span>
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-900/40 px-2 py-0.5 rounded">CHIẾN THẮNG</span>
                  </div>
                  <div className="text-xs text-slate-300">
                    &bull; Rank Dense: 2 &rarr; <code>1/(60 + 2) = 0.0161</code><br />
                    &bull; Rank Sparse: 2 &rarr; <code>1/(60 + 2) = 0.0161</code>
                  </div>
                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-emerald-400 font-bold">
                    <span>Tổng điểm RRF:</span>
                    <span className="text-base font-black">0.0322</span>
                  </div>
                </div>

                {/* Doc B: Single */}
                <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-300">Tài Liệu B (Chỉ đứng đầu 1 kênh)</span>
                    <span className="text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded">THUA ĐIỂM</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    &bull; Rank Dense: 1 &rarr; <code>1/(60 + 1) = 0.0163</code><br />
                    &bull; Rank Sparse: Không lọt top (None) &rarr; <code>0.0000</code>
                  </div>
                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-slate-400 font-bold">
                    <span>Tổng điểm RRF:</span>
                    <span className="text-base font-black">0.0163</span>
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 4: BƯỚC 3 - BGE-RERANKER & QUOTA (frames 1193 - 1420) */}
          {activeItem === 4 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-purple-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-purple-500/20 text-purple-300 font-bold border border-purple-500/40 flex items-center gap-2">
                      <Filter size={16} /> BƯỚC 3: BGE-RERANKER &amp; QUOTA DEDUPLICATION
                    </span>
                    <span className="text-xs font-mono text-purple-300 font-bold bg-purple-950/60 px-3 py-1 rounded-lg border border-purple-500/30">
                      Hạn Ngạch 2-8 Khối Cha
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Tái Xếp Hạng Chéo &amp; Chống Loãng Ngữ Cảnh
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-purple-400 block mb-1">Nguyên lý Quota Deduplication:</strong>
                    Mô hình Cross-Encoder BGE-Reranker-v2-m3 tái xếp hạng ứng viên cho từng truy vấn con. Để tránh tình trạng một Điều quy chế duy nhất có quá nhiều khối con chiếm trọn không gian ngữ cảnh, hệ thống áp dụng hạn ngạch Quota: Chỉ lấy tối đa 1 khối đại diện cho mỗi Điều, giữ tổng số khối từ 2 đến tối đa 8 khối cha chất lượng nhất.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-purple-950/30 border border-purple-500/30 rounded-2xl text-xs font-mono text-purple-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Reranker Architecture:</span>
                      <strong className="text-emerald-400">BGE-Reranker-v2-m3 FP16</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Quota Per Article:</span>
                      <strong className="text-emerald-400">Tối đa 1 khối / Điều quy chế</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Global Prompt Budget:</span>
                      <strong className="text-cyan-400">Từ 2 đến tối đa 8 khối cha</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-purple-300 flex items-center justify-between">
                    <span>Không làm loãng ngữ cảnh của mô hình ngôn ngữ lớn</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Quota Filtering Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-purple-400 font-bold flex items-center gap-1.5">
                    <Filter size={16} /> Quota Deduplication Filter
                  </span>
                  <span className="bg-purple-500/10 text-purple-400 px-2.5 py-0.5 rounded border border-purple-500/20 font-bold">
                    Quota: 2-8 Parents
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div>
                      <span className="text-white font-bold block">Điều 14 (Khối con 1 - Tiêu chí cảnh báo)</span>
                      <span className="text-[11px] text-slate-400">Score: 0.941 &bull; Parent ID: p_dieu_14</span>
                    </div>
                    <span className="text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded">CHỌN (#1)</span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-rose-950/20 border border-rose-500/30 flex items-center justify-between">
                    <div>
                      <span className="text-slate-400 block line-through">Điều 14 (Khối con 2 - Số tín chỉ đăng ký)</span>
                      <span className="text-[11px] text-rose-400">Score: 0.892 &bull; Trùng Điều 14 đã chọn</span>
                    </div>
                    <span className="text-rose-400 font-bold bg-rose-950/60 px-2 py-0.5 rounded">DEDUPLICATED</span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div>
                      <span className="text-white font-bold block">Điều 18 (Khối con 1 - Rút môn học học kỳ)</span>
                      <span className="text-[11px] text-slate-400">Score: 0.865 &bull; Parent ID: p_dieu_18</span>
                    </div>
                    <span className="text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded">CHỌN (#2)</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Tránh lặp thông tin và dành ngân sách token cho các Điều liên quan khác</span>
                  <span className="text-emerald-400 font-bold">Clean Context</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 5: BUNG NỞ KHỐI CHA - SMALL-TO-BIG (frames 1420 - 1690) */}
          {activeItem === 5 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-cyan-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40 flex items-center gap-2">
                      <Maximize2 size={16} /> BUNG NỞ KHỐI CHA: SMALL-TO-BIG MAPPING
                    </span>
                    <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-lg border border-cyan-500/30">
                      1.200 Tokens Legal Context
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Từ Khối Con 600 Ký Tự Bung Khối Cha Hoàn Chỉnh
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-cyan-400 block mb-1">Giải bài toán đánh đổi ngữ nghĩa:</strong>
                    Khối con nhỏ (600 ký tự) cho phép mô hình nhúng vector biểu diễn chính xác ý định tìm kiếm không bị nhiễu. Nhưng khi trả lời, nếu chỉ đưa 600 ký tự vào LLM, mô hình sẽ thiếu các điều kiện loại trừ và căn cứ pháp lý xung quanh. Cơ chế Small-to-Big tự động dùng ID khối cha để bung toàn văn 1.200 token vào prompt.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl text-xs font-mono text-cyan-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Retrieval Granularity:</span>
                      <strong className="text-emerald-400">Small (600 chars child chunk)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Generation Granularity:</span>
                      <strong className="text-emerald-400">Big (1.200 tokens parent article)</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Legal Context Loss:</span>
                      <strong className="text-emerald-400">0% (Đầy Đủ Căn Cứ Điều Khoản)</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-cyan-300 flex items-center justify-between">
                    <span>Mô hình luôn có đầy đủ ngữ cảnh để đưa ra câu trả lời chính xác</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Small-to-Big Mapping Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                    <Maximize2 size={16} /> Small-to-Big Parent Expansion
                  </span>
                  <span className="bg-cyan-500/10 text-cyan-400 px-2.5 py-0.5 rounded border border-cyan-500/20 font-bold">
                    Child &rarr; Parent
                  </span>
                </div>

                {/* Child Chunk */}
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-purple-400 font-bold">1. Khối Con Trúng Khớp (600 ký tự)</span>
                    <span className="text-slate-400">HNSW Vector Hit</span>
                  </div>
                  <p className="text-slate-300 text-xs">
                    "...sinh viên bị cảnh báo học vụ lần 1 chỉ được đăng ký tối đa 14 tín chỉ trong học kỳ kế tiếp..."
                  </p>
                </div>

                <div className="flex justify-center text-cyan-400">
                  <span className="text-xs font-mono font-bold">&darr; Tự động ánh xạ parent_id qua Parent Store &darr;</span>
                </div>

                {/* Parent Chunk */}
                <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/50 space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-emerald-400 font-bold">2. Khối Cha Hoàn Chỉnh (1.200 tokens) Nạp Vào Prompt</span>
                    <span className="text-emerald-300">Toàn Văn Điều 14</span>
                  </div>
                  <p className="text-slate-200 text-xs leading-relaxed">
                    "Điều 14: Cảnh báo học tập và Buộc thôi học. Khoản 1: Tiêu chuẩn xác định cảnh báo lần 1 (GPA &lt; 1.20)... Khoản 2: Giới hạn tín chỉ đăng ký tối đa 14 tín chỉ... Khoản 3: Thủ tục xét xóa cảnh báo nếu học kỳ tiếp theo đạt GPA &ge; 2.00..."
                  </p>
                </div>
              </div>
            </FloatingCard>
          )}

        </div>

      </SceneMotionWrapper>
    </div>
  );
};
