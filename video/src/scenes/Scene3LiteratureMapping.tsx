import React from 'react';
import { Audio, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { BookOpen, CheckCircle, Globe, Lightbulb, Scale, ShieldAlert, Sparkles, XCircle } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';

export const Scene3LiteratureMapping: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 5 Papers transition (Total 1713 frames ~ 57.12 seconds)
  // Sentence 0 (frames 0 - 121): Overview of 5 core papers
  // Sentence 1 (frames 130 - 546): Paper 1 - Rewrite-Retrieve-Read
  // Sentence 2 (frames 555 - 850): Paper 2 - Lost in the Middle
  // Sentence 3 (frames 859 - 1166): Paper 3 - Self-RAG
  // Sentence 4 (frames 1175 - 1457): Paper 4 - CF-RAG / Conflict Resolution
  // Sentence 5 (frames 1465 - 1705): Paper 5 - HyDE (Discarded)
  let activePaper = 0;
  if (frame >= 125 && frame < 550) activePaper = 1;
  else if (frame >= 550 && frame < 855) activePaper = 2;
  else if (frame >= 855 && frame < 1170) activePaper = 3;
  else if (frame >= 1170 && frame < 1460) activePaper = 4;
  else if (frame >= 1460) activePaper = 5;

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene3.mp3')} volume={1} />
      <AnimatedBackground theme="purple" />

      <SceneMotionWrapper durationInFrames={1713} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        {/* Compact Integrated Header Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/25">
              <BookOpen size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-purple-400">
                  SCIENTIFIC LITERATURE MAPPING
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; 5 CORE PAPERS IN /PAPER/</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                BẢN ĐỒ NGHIÊN CỨU: ÁP DỤNG ĐIỂM NÀO, LOẠI BỎ ĐIỂM NÀO?
              </h1>
            </div>
          </div>

          {/* Paper Carousel Badges */}
          <div className="flex items-center gap-2">
            {[
              { num: 1, name: 'Rewrite-Retrieve-Read' },
              { num: 2, name: 'Lost in Middle' },
              { num: 3, name: 'Self-RAG' },
              { num: 4, name: 'CF-RAG' },
              { num: 5, name: 'HyDE (BỎ)' }
            ].map((p) => (
              <span
                key={p.num}
                className={`text-xs font-mono font-bold px-3 py-1.5 rounded-xl border transition-all ${
                  activePaper === p.num
                    ? 'bg-purple-600 text-white border-purple-400 shadow-lg shadow-purple-500/30'
                    : 'bg-slate-900/80 text-slate-400 border-slate-800'
                }`}
              >
                P{p.num}: {p.name}
              </span>
            ))}
          </div>
        </div>

        {/* Carousel Paper Stage (Occupies ~75% of screen) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full">
          
          {/* OVERVIEW STAGE (0 - 4s / frames 0 - 125) */}
          {activePaper === 0 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-purple-500/50 rounded-3xl p-8 shadow-2xl flex flex-col items-center">
              <div className="text-center mb-6">
                <span className="text-xs font-mono px-3.5 py-1.5 rounded-full bg-purple-500/15 text-purple-400 font-bold border border-purple-500/30">
                  TỔNG HỢP CƠ SỞ KHOA HỌC
                </span>
                <h3 className="text-3xl font-black text-white mt-2">
                  5 Trụ Cột Nghiên Cứu Định Hình Kiến Trúc RAG Tại IUH
                </h3>
              </div>
              <div className="grid grid-cols-5 gap-5 w-full">
                <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 text-center">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold mx-auto mb-3">1</div>
                  <h4 className="text-sm font-bold text-white">Rewrite-Retrieve-Read</h4>
                  <p className="text-xs text-slate-400 mt-1">Microsoft Research</p>
                  <span className="inline-block mt-3 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-mono font-bold">Query Decomposition</span>
                </div>
                <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 text-center">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold mx-auto mb-3">2</div>
                  <h4 className="text-sm font-bold text-white">Lost in the Middle</h4>
                  <p className="text-xs text-slate-400 mt-1">Stanford / Berkeley</p>
                  <span className="inline-block mt-3 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-mono font-bold">Sandwich Reorder</span>
                </div>
                <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 text-center">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold mx-auto mb-3">3</div>
                  <h4 className="text-sm font-bold text-white">Self-RAG</h4>
                  <p className="text-xs text-slate-400 mt-1">Univ of Washington</p>
                  <span className="inline-block mt-3 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-mono font-bold">Reflection Quality Gate</span>
                </div>
                <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 text-center">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold mx-auto mb-3">4</div>
                  <h4 className="text-sm font-bold text-white">CF-RAG &amp; CRAG</h4>
                  <p className="text-xs text-slate-400 mt-1">DeepMind / USTC</p>
                  <span className="inline-block mt-3 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-mono font-bold">Conflict Priority</span>
                </div>
                <div className="bg-slate-950 p-5 rounded-2xl border border-rose-500/40 text-center">
                  <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold mx-auto mb-3">5</div>
                  <h4 className="text-sm font-bold text-white">HyDE</h4>
                  <p className="text-xs text-slate-400 mt-1">Carnegie Mellon</p>
                  <span className="inline-block mt-3 px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[11px] font-mono font-bold">LOẠI BỎ HOÀN TOÀN</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* PAPER 1: Rewrite-Retrieve-Read (frames 125 - 550) */}
          {activePaper === 1 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-slate-800 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono px-3.5 py-1.5 rounded bg-cyan-500/15 text-cyan-400 font-bold border border-cyan-500/30">
                    PAPER 1 &bull; MICROSOFT RESEARCH &amp; SJTU
                  </span>
                  <h3 className="text-3xl font-black text-white mt-3">
                    Rewrite-Retrieve-Read Framework
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Xinbei Ma, Yeyun Gong, Pengcheng He, Nan Duan, Daxin Jiang</p>
                  <p className="text-base text-slate-300 mt-4 leading-relaxed">
                    Nghiên cứu chỉ ra câu hỏi gốc của người học thường mơ hồ, chứa từ lóng hoặc kết hợp nhiều vế phức tạp, khiến tìm kiếm trực tiếp bị thất bại.
                  </p>
                </div>

                <div className="space-y-4 mt-6">
                  <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-2xl flex items-start gap-4">
                    <CheckCircle size={24} className="text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">DỰ ÁN ÁP DỤNG:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Phân rã câu hỏi kép thành tối đa 4 truy vấn con độc lập, chuẩn hóa từ khóa viết tắt học vụ trước khi tìm kiếm song song.
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-rose-950/40 border border-rose-500/40 rounded-2xl flex items-start gap-4">
                    <XCircle size={24} className="text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-rose-400 uppercase tracking-wider font-mono">ĐIỀU CHỈNH KỸ THUẬT:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Loại bỏ phương pháp học tăng cường PPO phức tạp và tốn kém; sử dụng ràng buộc JSON Schema trên mô hình ngôn ngữ lớn để đạt tốc độ xử lý siêu tốc.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Visual Demo */}
              <div className="w-1/2 bg-slate-950 border border-slate-800 rounded-3xl p-7 font-mono text-sm">
                <div className="text-cyan-400 font-bold mb-4 flex items-center justify-between">
                  <span>// Quy trình phân rã câu hỏi kép (Query Decomposition)</span>
                  <span className="text-xs text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">Unified Shared LLM</span>
                </div>
                <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-4 text-slate-300">
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-slate-400 font-bold block mb-1">User Query Gốc:</span>
                    <span className="text-amber-300 font-bold">"Học phí ngành CNTT K19 bao nhiêu và hạn đóng tiền học kỳ này khi nào?"</span>
                  </div>
                  <div className="pt-2 border-t border-slate-800 text-cyan-300 space-y-2">
                    <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/30">
                      <span className="text-slate-400 block text-xs mb-0.5">&rarr; Sub-Query 1 (Mức thu học phí):</span>
                      <strong className="text-cyan-200">"Học phí tín chỉ ngành Công nghệ thông tin khóa 19"</strong>
                    </div>
                    <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/30">
                      <span className="text-slate-400 block text-xs mb-0.5">&rarr; Sub-Query 2 (Lịch nộp học phí):</span>
                      <strong className="text-indigo-200">"Thời hạn nộp học phí học kỳ hiện tại theo thông báo phòng tài chính"</strong>
                    </div>
                  </div>
                </div>
                <div className="mt-5 text-emerald-400 text-xs font-mono flex items-center justify-between">
                  <span>&bull; Độc lập truy xuất song song trên PostgreSQL</span>
                  <span className="text-slate-400">Zero-Shot JSON Schema</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* PAPER 2: Lost in the Middle (frames 550 - 855) */}
          {activePaper === 2 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-slate-800 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono px-3.5 py-1.5 rounded bg-purple-500/15 text-purple-400 font-bold border border-purple-500/30">
                    PAPER 2 &bull; STANFORD, UC BERKELEY &amp; SAMAYA AI
                  </span>
                  <h3 className="text-3xl font-black text-white mt-3">
                    Lost in the Middle: How Language Models Use Long Contexts
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Nelson F. Liu, Kevin Lin, John Hewitt, Percy Liang...</p>
                  <p className="text-base text-slate-300 mt-3 leading-relaxed">
                    Transformer chú ý rất mạnh ở đầu và cuối ngữ cảnh, nhưng khả năng nhận thức bị sụt giảm từ 76% xuống dưới 54% ở khu vực chính giữa ngữ cảnh dài!
                  </p>
                </div>

                <div className="space-y-4 mt-5">
                  <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-2xl flex items-start gap-4">
                    <CheckCircle size={24} className="text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">DỰ ÁN ÁP DỤNG:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Thuật toán <code>_sandwich_reorder</code>: Hoán vị tài liệu rank 1 lên đầu, rank 2 xuống sát đáy theo mẫu <code>[#1, #3, #5, #4, #2]</code> kết hợp thẻ nhắc câu hỏi ở đáy.
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-rose-950/40 border border-rose-500/40 rounded-2xl flex items-start gap-4">
                    <XCircle size={24} className="text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-rose-400 uppercase tracking-wider font-mono">CHỦ ĐỘNG LOẠI BỎ:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Bỏ hoán vị vét cạn (brute-force permutation) nhiều lần vì làm tăng chi phí và độ trễ gọi LLM lên gấp bội mà không cải thiện tương xứng.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Real Chart Visual */}
              <div className="w-1/2 flex flex-col items-center">
                <div className="rounded-3xl overflow-hidden border-2 border-slate-700 bg-slate-950 p-4 shadow-2xl w-full">
                  <Img
                    src={staticFile('images/lost-in-the-middle-U-shaped performance curve.png')}
                    className="w-full h-[380px] object-contain rounded-2xl"
                  />
                  <div className="p-3 bg-slate-900/90 rounded-xl mt-3 text-center border border-slate-800">
                    <span className="text-sm font-mono text-purple-300 font-bold">
                      Đồ thị chữ U thực nghiệm (Stanford): Hiệu năng giảm sâu khi thông tin nằm ở giữa context
                    </span>
                  </div>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* PAPER 3: Self-RAG (frames 855 - 1170) */}
          {activePaper === 3 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-slate-800 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono px-3.5 py-1.5 rounded bg-indigo-500/15 text-indigo-400 font-bold border border-indigo-500/30">
                    PAPER 3 &bull; UNIV OF WASHINGTON &amp; ALLEN AI (2023)
                  </span>
                  <h3 className="text-3xl font-black text-white mt-3">
                    Self-RAG: Learning to Retrieve, Generate, and Critique
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Akari Asai, Sewon Min, Zexuan Zhong, Luke Zettlemoyer, Hannaneh Hajishirzi</p>
                  <p className="text-base text-slate-300 mt-4 leading-relaxed">
                    Self-RAG trang bị cho mô hình khả năng tự phản biện (Self-Reflection) đối với tài liệu trích xuất và câu trả lời sinh ra.
                  </p>
                </div>

                <div className="space-y-4 mt-6">
                  <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-2xl flex items-start gap-4">
                    <CheckCircle size={24} className="text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">DỰ ÁN ÁP DỤNG:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Tích hợp các thẻ tự đánh giá độ liên quan <code>&lt;doc_relevance&gt;</code> và độ tự tin <code>&lt;answer_confidence&gt;</code> trong khối suy nghĩ, làm chốt chặn an toàn cho bộ nhớ đệm Redis.
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-cyan-950/40 border border-cyan-500/40 rounded-2xl flex items-start gap-4">
                    <Lightbulb size={24} className="text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">ĐIỀU CHỈNH KỸ THUẬT:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Thay vì huấn luyện lại Special Tokens tốn kém, chúng tôi áp dụng XML Schema Structured Prompting trên các mô hình nền tảng có sẵn.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Visual Demo */}
              <div className="w-1/2 bg-slate-950 border border-slate-800 rounded-3xl p-7 font-mono text-sm">
                <div className="text-purple-400 font-bold mb-4 flex items-center justify-between">
                  <span>// Cấu trúc Self-RAG Reflection Block trong Production</span>
                  <span className="text-xs text-purple-300 px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30">Quality Gate</span>
                </div>
                <pre className="text-sm text-slate-200 bg-slate-900/90 p-5 rounded-2xl border border-slate-800 leading-relaxed font-mono">
{`<thinking>
  <doc_relevance>YES</doc_relevance>
  <conflict_detected>NO</conflict_detected>
  <answer_confidence>HIGH</answer_confidence>
</thinking>
<answer>
  Căn cứ Điều 15 Quy chế Đào tạo 2024, sinh viên bị cảnh báo học vụ
  lần 1 chỉ được đăng ký tối đa 14 tín chỉ trong học kỳ kế tiếp.
</answer>`}
                </pre>
                <div className="mt-5 text-emerald-400 text-xs font-mono flex items-center justify-between">
                  <span>✓ Điều kiện tiên quyết để được cấp phép ghi vào Redis Cache</span>
                  <span className="text-slate-400">Zero Hallucination Gate</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* PAPER 4: CF-RAG & Conflict Resolution (frames 1170 - 1460) */}
          {activePaper === 4 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-slate-800 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono px-3.5 py-1.5 rounded bg-amber-500/15 text-amber-400 font-bold border border-amber-500/30">
                    PAPER 4 &bull; CONFLICT RESOLUTION &amp; CORRECTIVE RAG
                  </span>
                  <h3 className="text-3xl font-black text-white mt-3">
                    Conflict-Free RAG &amp; Priority Rules
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Research on Conflict Resolution in Multi-Document Retrieval</p>
                  <p className="text-base text-slate-300 mt-4 leading-relaxed">
                    Xử lý mâu thuẫn giữa các văn bản quy chế ban hành ở các thời điểm khác nhau hoặc áp dụng cho các niên khóa khác nhau.
                  </p>
                </div>

                <div className="space-y-4 mt-6">
                  <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-2xl flex items-start gap-4">
                    <CheckCircle size={24} className="text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">DỰ ÁN ÁP DỤNG:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Thiết lập độ ưu tiên giải quyết mâu thuẫn văn bản: niên khóa sinh viên (Cohort) được ưu tiên cao nhất, kế đến là năm ban hành văn bản.
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-rose-950/40 border border-rose-500/40 rounded-2xl flex items-start gap-4">
                    <XCircle size={24} className="text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold text-rose-400 uppercase tracking-wider font-mono">KIÊN QUYẾT LOẠI BỎ WEB SEARCH:</span>
                      <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                        Quy chế đào tạo là văn bản nội bộ khép kín có tính pháp lý cao. Web Search bị loại bỏ hoàn toàn để tránh kéo về thông tin sai lệch từ các diễn đàn bên ngoài.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Visual Conflict Resolution Demo */}
              <div className="w-1/2 bg-slate-950 border border-slate-800 rounded-3xl p-7 font-mono text-sm flex flex-col justify-between">
                <div>
                  <div className="text-amber-400 font-bold mb-4 flex items-center justify-between">
                    <span>// Thứ tự giải quyết mâu thuẫn pháp lý (Priority Rules)</span>
                    <Scale size={20} className="text-amber-400" />
                  </div>
                  <div className="space-y-3">
                    <div className="p-3.5 rounded-2xl bg-emerald-950/50 border border-emerald-500/50 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-bold text-emerald-400 block">ƯU TIÊN 1 (CAO NHẤT):</span>
                        <span className="text-sm text-white font-bold">Niên khóa tuyển sinh (Cohort Matching)</span>
                      </div>
                      <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-300 rounded-lg text-xs font-bold">K19 áp quy chế K19</span>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-blue-950/50 border border-blue-500/50 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-bold text-blue-400 block">ƯU TIÊN 2:</span>
                        <span className="text-sm text-white font-bold">Năm ban hành văn bản (Issue Year)</span>
                      </div>
                      <span className="px-2.5 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-xs font-bold">2024 &gt; 2022</span>
                    </div>
                  </div>
                </div>
                <div className="mt-6 p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
                  <CheckCircle size={16} className="text-emerald-400 shrink-0" />
                  <span>Dập tắt hoàn toàn tình trạng áp nhầm quy chế mới cho sinh viên khóa cũ!</span>
                </div>
              </div>
            </FloatingCard>
          )}

          {/* PAPER 5: HyDE Discarded (frames 1460 - 1713) */}
          {activePaper === 5 && (
            <FloatingCard delay={0} floatOffset={0} className="w-full max-w-[1720px] bg-slate-900/95 border-2 border-rose-500/50 rounded-3xl p-8 shadow-2xl flex items-center gap-10">
              <div className="w-1/2 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono px-3.5 py-1.5 rounded bg-rose-500/15 text-rose-400 font-bold border border-rose-500/30">
                    PAPER 5 &bull; CARNEGIE MELLON &amp; UNIV OF WATERLOO (2022)
                  </span>
                  <h3 className="text-3xl font-black text-white mt-3">
                    Hypothetical Document Embeddings (HyDE)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan</p>
                  <p className="text-base text-slate-300 mt-4 leading-relaxed">
                    HyDE yêu cầu LLM tự bịa ra một đoạn văn bản giả định (Hypothetical Document) rồi mới dùng vector của nó đi tìm tài liệu thật.
                  </p>
                </div>

                <div className="p-5 bg-rose-950/50 border border-rose-500/50 rounded-2xl mt-6">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-base mb-2 font-mono">
                    <ShieldAlert size={22} /> TẠI SAO LOẠI BỎ HYDE TRONG QUY CHẾ HỌC VỤ?
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    Khi LLM đoán mò số tín chỉ hoặc mức điểm rèn luyện giả định (ví dụ bịa ra 'dưới 16 tín chỉ' thay vì '14'), vector của đoạn giả định này sẽ kéo về các điều khoản hoàn toàn sai lệch!
                  </p>
                </div>

                <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-2xl mt-4 flex items-center gap-3 text-sm text-emerald-300 font-mono">
                  <CheckCircle size={20} /> Thay thế bằng: <span className="font-bold">Hierarchical Augmented Context + Table-Aware Splitter</span>
                </div>
              </div>

              {/* Visual Warning */}
              <div className="w-1/2 bg-slate-950 border border-slate-800 rounded-3xl p-8 flex flex-col items-center justify-center text-center">
                <div className="w-20 h-20 rounded-full bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-5 p-4">
                  <XCircle size={48} />
                </div>
                <h4 className="text-2xl font-bold text-white">HyDE Gây Ảo Giác Trong Pháp Lý</h4>
                <p className="text-base text-slate-300 mt-3 max-w-[480px] leading-relaxed">
                  Trong văn bản pháp luật và quy chế đại học, mọi con số đều là ranh giới tuyệt đối. Đoán mò trước khi tìm kiếm là hành vi đầu độc vector nguy hiểm nhất!
                </p>
                <div className="mt-6 px-5 py-2 rounded-full bg-rose-950 text-rose-300 text-sm font-mono font-bold border border-rose-700">
                  LOẠI BỎ HOÀN TOÀN KHỎI KIẾN TRÚC IUH CHATBOT
                </div>
              </div>
            </FloatingCard>
          )}

        </div>
      </SceneMotionWrapper>
    </div>
  );
};
