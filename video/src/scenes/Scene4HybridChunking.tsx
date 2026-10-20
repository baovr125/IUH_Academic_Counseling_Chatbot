import React from 'react';
import { Audio, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Database, FileCode, Layers, Sparkles, Table, Tag, CheckCircle2, Binary, Cpu, FileText, Split, Compass } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';

export const Scene4HybridChunking: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Active section calibrated to sentenceTimings.json (Total 1790 frames ~ 59.67s):
  // Sentence 0 (frames 0 - 301): Overview & Ingestion Stats (1,445 parents, 3,252 children)
  // Sentence 1 (frames 310 - 536): Mục 1 - YAML Frontmatter Metadata & Breadcrumbs
  // Sentence 2 (frames 544 - 1000): Mục 2 - Parent Chunking H1-H6 1200t & Regex Fallback
  // Sentence 3 (frames 1008 - 1365): Mục 3 - Table-Aware Header Cloning
  // Sentence 4 (frames 1373 - 1781): Mục 4 - Child Chunks 600c & Bi-Encoder 768d ONNX CUDA
  let activeItem = 0;
  if (frame >= 305 && frame < 540) activeItem = 1;
  else if (frame >= 540 && frame < 1004) activeItem = 2;
  else if (frame >= 1004 && frame < 1370) activeItem = 3;
  else if (frame >= 1370) activeItem = 4;

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene4.mp3')} volume={1} />
      <AnimatedBackground theme="emerald" />

      <SceneMotionWrapper durationInFrames={1790} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        {/* Compact Integrated Header Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Layers size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-cyan-400">
                  DATA INGESTION PIPELINE
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; APP/DATA_INGESTION/CHUNKERS/HYBRID_CHUNKER.PY</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                KỸ NGHỆ DỮ LIỆU ĐẦU VÀO: HYBRID PARENT-CHILD &amp; TABLE-AWARE
              </h1>
            </div>
          </div>

          {/* Carousel Stage Badges */}
          <div className="flex items-center gap-2">
            {[
              { num: 0, label: 'Tổng quan (1.445 Cha / 3.252 Con)' },
              { num: 1, label: 'Mục 1: Frontmatter & Breadcrumbs' },
              { num: 2, label: 'Mục 2: Parent Chunks (1.200t)' },
              { num: 3, label: 'Mục 3: Table-Aware Header' },
              { num: 4, label: 'Mục 4: Child Chunks & Vector 768d' }
            ].map((s) => (
              <span
                key={s.num}
                className={`text-xs font-mono font-bold px-3 py-1.5 rounded-xl border transition-colors ${
                  activeItem === s.num
                    ? 'bg-cyan-600 text-white border-cyan-400 shadow-lg shadow-cyan-500/30'
                    : 'bg-slate-900/80 text-slate-400 border-slate-800'
                }`}
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {/* Database Real Stats Strip */}
        <div className="w-full max-w-[1780px] mx-auto bg-slate-900/95 border-2 border-slate-800 rounded-2xl px-6 py-2.5 shadow-xl font-mono text-xs flex items-center justify-between my-1">
          <div className="flex items-center gap-2 text-slate-300">
            <Database size={16} className="text-cyan-400" />
            <span>Thực Tế Cơ Sở Dữ Liệu PostgreSQL (Học kỳ 1 năm học 2024-2025):</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-slate-300">Khối cha (Parent Chunks): <strong className="text-emerald-400 text-sm">1.445</strong></span>
            <span className="text-slate-300">Khối con (Child Chunks): <strong className="text-cyan-400 text-sm">3.252</strong></span>
            <span className="text-slate-300">Embedding: <strong className="text-purple-400">vietnamese-bi-encoder (768d)</strong></span>
            <span className="text-slate-300">Tăng tốc: <strong className="text-amber-400">ONNX Runtime / CUDA</strong></span>
          </div>
        </div>

        {/* Main Single-Focus Stage Area (Occupies ~75% screen) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full">
          
          {/* STAGE 0: OVERVIEW & INGESTION STATS (frames 0 - 305) */}
          {activeItem === 0 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-cyan-500/50 rounded-3xl p-8 shadow-2xl flex flex-col items-center">
              <div className="text-center mb-6">
                <span className="text-xs font-mono px-3.5 py-1.5 rounded-full bg-cyan-500/15 text-cyan-400 font-bold border border-cyan-500/30">
                  TIỀN XỬ LÝ &amp; CHUẨN HÓA DỮ LIỆU HỌC VỤ
                </span>
                <h3 className="text-3xl font-black text-white mt-2">
                  Tầng Dữ Liệu: 1.445 Khối Cha &amp; 3.252 Khối Con Trong PostgreSQL
                </h3>
                <p className="text-sm text-slate-300 mt-1">
                  Đảm bảo văn bản quy chế phức tạp được phân cấp khoa học, không đứt gãy bảng biểu và giữ nguyên trọn vẹn ngữ cảnh.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-8 w-full max-w-[1400px]">
                <div className="bg-slate-950 p-6 rounded-3xl border border-slate-800 flex items-center gap-6">
                  <Img src={staticFile('images/banner_camnang.png')} className="w-56 h-36 object-cover rounded-2xl border border-slate-700 shrink-0" />
                  <div>
                    <span className="text-xs font-mono text-cyan-400 font-bold uppercase">Nguồn tài liệu 1</span>
                    <h4 className="text-xl font-black text-white mt-1">Cẩm Nang Người Học IUH</h4>
                    <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                      Chứa các bảng biểu phức tạp về mức học phí từng tín chỉ theo ngành, biểu mẫu thủ tục và lịch trình đóng tiền học kỳ.
                    </p>
                    <div className="mt-3 text-[11px] font-mono text-emerald-400 font-bold">
                      &bull; Đã bóc tách cấu trúc Markdown + Table-Aware
                    </div>
                  </div>
                </div>

                <div className="bg-slate-950 p-6 rounded-3xl border border-slate-800 flex items-center gap-6">
                  <Img src={staticFile('images/sotaysinhvien.jpg')} className="w-56 h-36 object-cover rounded-2xl border border-slate-700 shrink-0" />
                  <div>
                    <span className="text-xs font-mono text-purple-400 font-bold uppercase">Nguồn tài liệu 2</span>
                    <h4 className="text-xl font-black text-white mt-1">Sổ Tay Sinh Viên Chính Quy</h4>
                    <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                      Quy chế đào tạo theo hệ thống tín chỉ, điều kiện cảnh báo học vụ, chuẩn đầu ra ngoại ngữ và tiêu chuẩn tốt nghiệp.
                    </p>
                    <div className="mt-3 text-[11px] font-mono text-purple-400 font-bold">
                      &bull; Phân cấp Parent-Child 1.200t &bull; Breadcrumbs
                    </div>
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 1: MỤC 1 - YAML FRONTMATTER & BREADCRUMBS (frames 305 - 540) */}
          {activeItem === 1 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-cyan-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40 flex items-center gap-2">
                      <Tag size={16} /> MỤC 1: TRÍCH XUẤT YAML FRONTMATTER
                    </span>
                    <span className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/60 px-3 py-1 rounded-lg border border-cyan-500/30">
                      app/data_ingestion/chunkers/hybrid_chunker.py
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Siêu Dữ Liệu Phần Đầu &amp; Đường Dẫn Breadcrumb
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-cyan-400 block mb-1">Mục đích kỹ thuật:</strong>
                    Mỗi văn bản Markdown đầu vào bắt buộc phải có phần đầu YAML Frontmatter lưu trữ URL nguồn chính thức, tiêu đề tài liệu, và chuỗi breadcrumb điều hướng. Nhờ đó, bất kỳ khối dữ liệu nhỏ nào sau này cũng biết chính xác nó thuộc văn bản nào.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl text-xs font-mono text-cyan-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Source URL Traceability:</span>
                      <strong className="text-emerald-400">100% CÓ CĂN CỨ</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Breadcrumbs Navigation:</span>
                      <strong className="text-emerald-400">Phòng Đào tạo &gt; Quy chế</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Cohort Isolation:</span>
                      <strong className="text-emerald-400">Khóa K19, K20, K21 Rạch Ròi</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-cyan-300 flex items-center justify-between">
                    <span>Đảm bảo căn cứ pháp lý minh bạch cho từng câu trả lời</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Frontmatter YAML Code Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                    <FileCode size={16} /> Header YAML Trích Xuất Từ Markdown
                  </span>
                  <span className="bg-cyan-500/10 text-cyan-400 px-2.5 py-0.5 rounded border border-cyan-500/20 font-bold">
                    Validated Frontmatter
                  </span>
                </div>
                <div className="pt-4 space-y-2 text-slate-200 text-sm leading-relaxed overflow-x-auto">
                  <div className="text-slate-500 font-bold">---</div>
                  <div><span className="text-purple-400">title</span>: <span className="text-amber-300">"Quy chế Đào tạo Học vụ Tín chỉ"</span></div>
                  <div><span className="text-purple-400">source_url</span>: <span className="text-cyan-300">"https://daotao.iuh.edu.vn/quy-che-2024"</span></div>
                  <div><span className="text-purple-400">effective_year</span>: <span className="text-emerald-300">2024</span></div>
                  <div><span className="text-purple-400">target_cohorts</span>: [<span className="text-emerald-300">"K19", "K20", "K21"</span>]</div>
                  <div>
                    <span className="text-purple-400">breadcrumb</span>: <span className="text-amber-300">"Trang chủ &gt; Quy chế đào tạo &gt; Chương 3 &gt; Điều 14"</span>
                  </div>
                  <div><span className="text-purple-400">doc_type</span>: <span className="text-cyan-300">"ACADEMIC_REGULATION"</span></div>
                  <div className="text-slate-500 font-bold">---</div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Trích xuất tự động qua regex YAML trước khi đưa vào phân tách</span>
                  <span className="text-emerald-400 font-bold">Metadata Injected</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 2: MỤC 2 - PARENT CHUNKS 1200T & REGEX FALLBACK (frames 540 - 1004) */}
          {activeItem === 2 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-indigo-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/40 flex items-center gap-2">
                      <Layers size={16} /> MỤC 2: PHÂN CẤP KHỐI CHA (PARENT CHUNKS)
                    </span>
                    <span className="text-xs font-mono text-indigo-300 font-bold bg-indigo-950/60 px-3 py-1 rounded-lg border border-indigo-500/30">
                      Ngưỡng 1.200 Tokens
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Bóc Tách Khối Cha Theo Tiêu Đề H1-H6 &amp; Regex Fallback
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-indigo-400 block mb-1">Thuật toán chia tách phân cấp:</strong>
                    Tài liệu được bóc tách theo các tiêu đề Markdown từ H1 đến H6 (tương ứng từng Chương, Điều). Chỉ khi một phần quy chế quá dài vượt quá ngưỡng 1.200 token, thuật toán mới kích hoạt biểu thức chính quy (Regex Fallback) để nhận diện các mục số La Mã hoặc đề mục in đậm, kết hợp ngắt theo đoạn văn.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-indigo-950/30 border border-indigo-500/30 rounded-2xl text-xs font-mono text-indigo-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Heading Boundaries:</span>
                      <strong className="text-emerald-400">H1, H2, H3, H4, H5, H6</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Parent Token Budget:</span>
                      <strong className="text-emerald-400">Tối đa 1.200 Tokens / Khối</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Fallback Trigger:</span>
                      <strong className="text-amber-400">Regex Roman &bull; Bold Subsections</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-indigo-300 flex items-center justify-between">
                    <span>Không bao giờ cắt xén cụt dòng giữa chừng</span>
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  </div>
                </div>
              </div>

              {/* Hierarchy Tree Visualization */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                    <Compass size={16} /> Cấu Trúc Khối Cha (Parent Store)
                  </span>
                  <span className="bg-indigo-500/10 text-indigo-400 px-2.5 py-0.5 rounded border border-indigo-500/20 font-bold">
                    PostgreSQL 16
                  </span>
                </div>
                <div className="pt-4 space-y-3 text-slate-200 text-sm leading-relaxed">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <div className="text-indigo-400 font-bold"># CHƯƠNG III: QUY TRÌNH HỌC VỤ VÀ XẾP HẠNG (H1)</div>
                    <div className="pl-4 mt-2 text-cyan-300 font-bold">## Điều 14: Cảnh báo kết quả học tập (H2)</div>
                    <div className="pl-8 text-xs text-slate-300 mt-1 leading-normal">
                      Toàn văn Điều 14 gồm Khoản 1 (Tiêu chí cảnh báo lần 1), Khoản 2 (Số tín chỉ tối đa được đăng ký: 14 tín chỉ), Khoản 3 (Buộc thôi học).
                    </div>
                    <div className="pl-8 mt-2 flex items-center gap-3 text-[11px] text-emerald-400">
                      <span>✓ Dung lượng: 840 tokens (&lt; 1200t threshold)</span>
                      <span>✓ Lưu nguyên vẹn thành 1 Parent Chunk</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/60 border border-amber-500/30 text-xs text-amber-200">
                    <strong>Trường hợp vượt ngưỡng (&gt; 1200t):</strong> Tự động tách theo <code>r'^(I|II|III|IV|V)\.\s'</code> hoặc <code>r'^\*\*(.*?)\*\*'</code> mà không làm mất liên kết cha con.
                  </div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>Khối cha dùng để nạp toàn vẹn vào prompt khi trúng khối con</span>
                  <span className="text-emerald-400 font-bold">1.445 Parents In Store</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 3: MỤC 3 - TABLE-AWARE HEADER CLONING (frames 1004 - 1370) */}
          {activeItem === 3 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-emerald-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40 flex items-center gap-2">
                      <Table size={16} /> MỤC 3: TABLE-AWARE HEADER CLONING
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-500/30">
                      Đặc Biệt Cho Quy Chế IUH
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Nhân Bản Dòng Tiêu Đề Cột Vào Từng Khối Con
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-emerald-400 block mb-1">Giải pháp cho tử huyệt cắt bảng:</strong>
                    Trong RAG thông thường, khi một bảng biểu bị cắt ngang, các dòng điểm số hay mức học phí ở dưới sẽ biến thành những con số trơ trọi không có tiêu đề cột. Bộ tách Table-Aware phát hiện cú pháp bảng biểu và tự động sao chép nguyên vẹn dòng tiêu đề cột vào đầu mỗi khối con.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl text-xs font-mono text-emerald-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Table Header Preservation:</span>
                      <strong className="text-emerald-400">100% NHÂN BẢN</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Row Context Semantic:</span>
                      <strong className="text-emerald-400">BẢO TOÀN TRỌN VẸN</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Tuition &amp; GPA Lookups:</span>
                      <strong className="text-emerald-400">ZERO AMBIGUITY</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
                    <span>Không bao giờ bị mất ý nghĩa của các con số học phí và điểm số</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>

              {/* Before/After Table Comparison */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl space-y-4">
                {/* Bad Case: Naive Cut */}
                <div className="p-3 rounded-2xl bg-rose-950/20 border border-rose-500/40">
                  <div className="text-rose-400 font-bold flex items-center justify-between mb-2">
                    <span>&times; RAG Cơ Bản (Naive): Cắt ngang bảng ngẫu nhiên</span>
                    <span className="text-[10px] bg-rose-500/20 px-2 py-0.5 rounded text-rose-300">MẤT NGỮ NGHĨA</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-[11px] text-slate-400 font-mono">
                    <div>| Công nghệ thông tin | 980.000 VNĐ | 3 tín chỉ |</div>
                    <div className="text-rose-400 italic mt-1">&rarr; Mô hình không biết 980.000 VNĐ là học phí 1 tín chỉ hay học phí cả môn!</div>
                  </div>
                </div>

                {/* Good Case: Table-Aware */}
                <div className="p-3 rounded-2xl bg-emerald-950/30 border border-emerald-500/50">
                  <div className="text-emerald-400 font-bold flex items-center justify-between mb-2">
                    <span>✓ Table-Aware IUH: Tự động nhân bản dòng tiêu đề cột</span>
                    <span className="text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-300">CHÍNH XÁC 100%</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-[11px] text-slate-200 font-mono space-y-1">
                    <div className="text-cyan-300 font-bold">| Tên Ngành | Mức Thu 1 Tín Chỉ | Số TC Chuẩn |</div>
                    <div className="text-slate-500">|---|---|---|</div>
                    <div className="text-emerald-300">| Công nghệ thông tin | 980.000 VNĐ | 3 tín chỉ |</div>
                    <div className="text-emerald-400 font-bold pt-1 border-t border-slate-800">
                      &rarr; Mô hình hiểu ngay: 980.000 VNĐ là mức thu trên 1 tín chỉ của ngành CNTT.
                    </div>
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* STAGE 4: MỤC 4 - CHILD CHUNKS & BI-ENCODER 768D (frames 1370 - 1790) */}
          {activeItem === 4 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-purple-500/60 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono px-3.5 py-1.5 rounded-xl bg-purple-500/20 text-purple-300 font-bold border border-purple-500/40 flex items-center gap-2">
                      <Binary size={16} /> MỤC 4: KHỐI CON (CHILD CHUNKS 600C) &amp; VECTOR 768D
                    </span>
                    <span className="text-xs font-mono text-purple-300 font-bold bg-purple-950/60 px-3 py-1 rounded-lg border border-purple-500/30">
                      ONNX Runtime CUDA
                    </span>
                  </div>
                  <h3 className="text-3xl font-black text-white mt-2">
                    Khối Con 600 Ký Tự Gối Đầu &amp; Vector 768 Chiều
                  </h3>
                  
                  <div className="mt-5 p-4 rounded-2xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    <strong className="text-purple-400 block mb-1">Thông số kỹ thuật khối con:</strong>
                    Mỗi khối con có kích thước tối đa 600 ký tự với độ gối đầu (overlap) 100 ký tự để không làm mất các từ nối giữa các câu. Mỗi khối con được gắn tiền tố breadcrumb và mã hóa thành vector 768 chiều bởi mô hình Bi-Encoder tiếng Việt tối ưu bằng ONNX Runtime trên GPU CUDA.
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <div className="p-3.5 bg-purple-950/30 border border-purple-500/30 rounded-2xl text-xs font-mono text-purple-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span>&bull; Chunk Size / Overlap:</span>
                      <strong className="text-emerald-400">600 characters / 100 overlap</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Total Ingested Child Chunks:</span>
                      <strong className="text-cyan-400">3.252 Khối Con Trong Database</strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>&bull; Neural Embedding Model:</span>
                      <strong className="text-purple-400">vietnamese-bi-encoder (768d FP16)</strong>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
                    <span>Tìm kiếm ngữ nghĩa siêu chính xác, không nhầm lẫn</span>
                    <CheckCircle2 size={18} />
                  </div>
                </div>
              </div>

              {/* PostgreSQL Record Display */}
              <div className="w-1/2 bg-slate-950 border-2 border-slate-800 rounded-3xl p-6 font-mono text-xs shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-xs">
                  <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                    <Database size={16} /> PostgreSQL pgvector: child_chunks Table
                  </span>
                  <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-0.5 rounded border border-emerald-500/20 font-bold">
                    HNSW Cosine Index
                  </span>
                </div>
                <div className="pt-4 space-y-2.5 text-slate-200 text-sm leading-relaxed overflow-x-auto">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1 text-xs">
                    <div><span className="text-purple-400">id</span>: <span className="text-slate-400">"c_8f9a2b"</span></div>
                    <div><span className="text-purple-400">parent_id</span>: <span className="text-cyan-400">"p_ điều_14_canh_bao"</span></div>
                    <div>
                      <span className="text-purple-400">breadcrumb</span>: <span className="text-amber-300">"Quy chế &gt; Điểm số &gt; Điều 14"</span>
                    </div>
                    <div>
                      <span className="text-purple-400">content</span>: <span className="text-slate-300">"[Điều 14] Sinh viên bị cảnh báo học vụ lần 1 chỉ được phép đăng ký tối đa 14 tín chỉ trong học kỳ tiếp theo..."</span>
                    </div>
                    <div className="pt-1 text-emerald-400">
                      <span className="text-purple-400">embedding</span>: <span className="text-emerald-300">[-0.0421, 0.0812, 0.0194, ... 768 dims]</span>
                    </div>
                  </div>
                </div>
                <div className="mt-6 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>HNSW m=16, ef_construction=64 cho truy vấn dưới 2ms</span>
                  <span className="text-emerald-400 font-bold">3.252 Chunks Indexed</span>
                </div>
              </div>
            </FloatingCard>
          )}

        </div>

      </SceneMotionWrapper>
    </div>
  );
};
