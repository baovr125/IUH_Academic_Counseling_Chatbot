import React from 'react';
import { Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { AlertTriangle, BookOpen, Bot, CheckCircle2, FileQuestion, Flame, Lock, Scissors, ShieldAlert, Sparkles, XCircle } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';

export const Scene1Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase transitions across 1305 frames (~43.5 seconds) calibrated to audio sentences:
  // Phase 1 (frames 0 - 325): Real IUH Campus & Academic Documents (Sentence 0: 0 - 322)
  // Phase 2 (frames 325 - 1145): The 3 Fatal Flaws of Naive RAG (Sentences 1 - 4: 330 - 1144)
  // Phase 3 (frames 1145 - 1305): Academic Chatbot Service Mission (Sentence 5: 1152 - 1296)
  const phase1Opacity = interpolate(frame, [0, 20, 310, 325], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const phase2Opacity = interpolate(frame, [325, 340, 1130, 1145], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const phase3Opacity = interpolate(frame, [1145, 1160], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Flaw card active highlights matching sentences 2, 3, 4:
  // Sentence 2 (frames 512 - 697): Flaw 1
  // Sentence 3 (frames 705 - 941): Flaw 2
  // Sentence 4 (frames 949 - 1144): Flaw 3
  const isFlaw1Active = frame >= 512 && frame < 700;
  const isFlaw2Active = frame >= 700 && frame < 945;
  const isFlaw3Active = frame >= 945;

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene1.mp3')} volume={1} />
      <AnimatedBackground theme="blue" />

      <SceneMotionWrapper durationInFrames={1305} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        
        {/* Compact Integrated Title Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Bot size={22} className="text-white" />
            </div>
            <div>
              <span className="text-xs font-mono font-bold text-cyan-400">IUH ACADEMIC COUNSELING CHATBOT SERVICE</span>
              <h1 className="text-2xl font-black text-white tracking-tight">
                TỬ HUYỆT CỦA NAIVE RAG TRONG TƯ VẤN HỌC VỤ ĐẠI HỌC
              </h1>
            </div>
          </div>
          <span className="text-xs font-mono bg-rose-500/15 text-rose-400 font-bold px-3 py-1 rounded-full border border-rose-500/30 flex items-center gap-1.5">
            <Flame size={14} /> Problem Analysis &amp; Motivation
          </span>
        </div>

        {/* Main Full-Size Content Area (Occupies ~75% of screen) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full">
          
          {/* PHASE 1: Real Campus & Document Sources (0 - 10.8s / frames 0 - 325) */}
          {frame < 330 && (
            <div style={{ opacity: phase1Opacity }} className="w-full flex items-center justify-between gap-8 px-4">
              {/* Campus Real Shot */}
              <FloatingCard delay={0} floatOffset={0} className="w-1/2 flex flex-col items-center">
                <div className="relative rounded-3xl overflow-hidden border-2 border-slate-700/80 shadow-2xl group w-full">
                  <Img
                    src={staticFile('images/anh-nha-E-iuh.jpg')}
                    className="w-full h-[520px] object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent" />
                  <div className="absolute bottom-6 left-8 right-8">
                    <div className="inline-block px-3 py-1 rounded-lg bg-cyan-500 text-slate-950 font-black text-xs uppercase tracking-wider mb-2">
                      Cơ sở chính IUH &bull; Số 12 Nguyễn Văn Bảo, Gò Vấp, TP.HCM
                    </div>
                    <h3 className="text-2xl font-black text-white">Nhà E — Trụ sở Ban Giám hiệu &amp; Phòng Đào tạo</h3>
                    <p className="text-sm text-slate-200 mt-1">Nơi giải quyết toàn bộ thủ tục học vụ, quy chế và tốt nghiệp của hàng vạn sinh viên.</p>
                  </div>
                </div>
              </FloatingCard>

              {/* Official Academic Documents Showcase */}
              <div className="w-1/2 flex flex-col gap-6 justify-center">
                <FloatingCard delay={8} floatOffset={1} className="bg-slate-900/95 border-2 border-slate-800 rounded-3xl p-5 shadow-2xl flex items-center gap-6">
                  <Img src={staticFile('images/banner_camnang.png')} className="w-64 h-36 object-cover rounded-2xl border border-slate-700" />
                  <div className="flex-1">
                    <div className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">Tài liệu chính quy 1</div>
                    <h4 className="text-xl font-black text-white mt-1">Cẩm Nang Người Học IUH</h4>
                    <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                      Hàng trăm trang quy định đào tạo tín chỉ, biểu mức học phí và điều kiện xét tốt nghiệp chính thức.
                    </p>
                  </div>
                </FloatingCard>

                <FloatingCard delay={16} floatOffset={2} className="bg-slate-900/95 border-2 border-slate-800 rounded-3xl p-5 shadow-2xl flex items-center gap-6">
                  <Img src={staticFile('images/sotaysinhvien.jpg')} className="w-64 h-36 object-cover rounded-2xl border border-slate-700" />
                  <div className="flex-1">
                    <div className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-wider">Tài liệu chính quy 2</div>
                    <h4 className="text-xl font-black text-white mt-1">Sổ Tay Sinh Viên</h4>
                    <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                      Hướng dẫn chi tiết quy trình khiếu nại điểm, bảo lưu, học lại và chuẩn đầu ra ngoại ngữ cập nhật liên tục theo khóa.
                    </p>
                  </div>
                </FloatingCard>
              </div>
            </div>
          )}

          {/* PHASE 2: The 3 Fatal Flaws of Naive RAG (10.8s - 38.2s / frames 325 - 1145) */}
          {frame >= 325 && frame < 1150 && (
            <div style={{ opacity: phase2Opacity }} className="w-full max-w-[1720px] flex flex-col items-center">
              <div className="text-center mb-6">
                <span className="text-xs font-mono px-3.5 py-1.5 rounded-full bg-rose-500/15 text-rose-400 font-bold border border-rose-500/30">
                  PHÂN TÍCH HỆ THỐNG &bull; NAIVE RAG PITFALLS
                </span>
                <h3 className="text-3xl font-black text-white mt-2">
                  3 Tử Huyệt Của Naive RAG Trong Dữ Liệu Học Vụ Đại Học
                </h3>
              </div>

              <div className="grid grid-cols-3 gap-7 w-full">
                {/* Flaw 1: Context Truncation */}
                <FloatingCard
                  delay={0}
                  floatOffset={0}
                  className={`rounded-3xl p-7 shadow-2xl flex flex-col justify-between transition-colors duration-300 border-2 ${
                    isFlaw1Active
                      ? 'bg-rose-950/70 border-rose-400 shadow-2xl shadow-rose-500/25'
                      : 'bg-slate-900/95 border-slate-800'
                  }`}
                >
                  <div>
                    <div className="w-14 h-14 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center mb-4 border border-rose-500/30">
                      <Scissors size={30} />
                    </div>
                    <div className="text-xs font-mono text-rose-400 font-bold uppercase tracking-wider">Tử Huyệt 1</div>
                    <h4 className="text-xl font-black text-white mt-1">Đứt Gãy Ngữ Cảnh Bảng Biểu</h4>
                    <p className="text-xs font-mono text-slate-400 mt-1">Context Truncation &amp; Chunk Fragmentation</p>
                    <p className="text-sm text-slate-300 mt-4 leading-relaxed">
                      Việc cắt nhỏ văn bản cố định (Fixed-size Chunking) làm đứt gãy mối liên kết giữa các hàng và cột trong bảng biểu điều kiện tốt nghiệp, mức thu học phí và bảng quy đổi điểm rèn luyện.
                    </p>
                  </div>
                  <div className="mt-6 pt-3 border-t border-slate-800/80 text-xs font-mono text-rose-400 font-bold">
                    &bull; Hậu quả: Mất điều kiện loại trừ, số liệu bị tách rời ngữ cảnh
                  </div>
                </FloatingCard>

                {/* Flaw 2: Temporal Mismatch & Hallucination */}
                <FloatingCard
                  delay={6}
                  floatOffset={1}
                  className={`rounded-3xl p-7 shadow-2xl flex flex-col justify-between transition-colors duration-300 border-2 ${
                    isFlaw2Active
                      ? 'bg-amber-950/70 border-amber-400 shadow-2xl shadow-amber-500/25'
                      : 'bg-slate-900/95 border-slate-800'
                  }`}
                >
                  <div>
                    <div className="w-14 h-14 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center mb-4 border border-amber-500/30">
                      <ShieldAlert size={30} />
                    </div>
                    <div className="text-xs font-mono text-amber-400 font-bold uppercase tracking-wider">Tử Huyệt 2</div>
                    <h4 className="text-xl font-black text-white mt-1">Ảo Giác Quy Chế Cũ và Mới</h4>
                    <p className="text-xs font-mono text-slate-400 mt-1">Temporal Conflict &amp; Severe Hallucination</p>
                    <p className="text-sm text-slate-300 mt-4 leading-relaxed">
                      Mô hình dễ nhầm lẫn giữa các văn bản quy chế qua các năm ban hành. Hậu quả là sinh viên khóa cũ bị áp nhầm quy chế tốt nghiệp của khóa mới, gây sai lệch nghiêm trọng về quyền lợi đào tạo.
                    </p>
                  </div>
                  <div className="mt-6 pt-3 border-t border-slate-800/80 text-xs font-mono text-amber-400 font-bold">
                    &bull; Hậu quả: Sinh viên bị tư vấn sai hạn tốt nghiệp &amp; chuẩn đầu ra
                  </div>
                </FloatingCard>

                {/* Flaw 3: Prompt Injection */}
                <FloatingCard
                  delay={12}
                  floatOffset={2}
                  className={`rounded-3xl p-7 shadow-2xl flex flex-col justify-between transition-colors duration-300 border-2 ${
                    isFlaw3Active
                      ? 'bg-purple-950/70 border-purple-400 shadow-2xl shadow-purple-500/25'
                      : 'bg-slate-900/95 border-slate-800'
                  }`}
                >
                  <div>
                    <div className="w-14 h-14 rounded-2xl bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4 border border-purple-500/30">
                      <Lock size={30} />
                    </div>
                    <div className="text-xs font-mono text-purple-400 font-bold uppercase tracking-wider">Tử Huyệt 3</div>
                    <h4 className="text-xl font-black text-white mt-1">Lỗ Hổng Prompt Injection</h4>
                    <p className="text-xs font-mono text-slate-400 mt-1">Adversarial Prompting &amp; Context Leak</p>
                    <p className="text-sm text-slate-300 mt-4 leading-relaxed">
                      Không có cơ chế cô lập ngữ cảnh, kẻ xấu hoặc sinh viên có thể thực hiện tiêm mã prompt injection, chèn thẻ đóng giả mạo để lừa mô hình xác nhận sai kết quả học tập hoặc cấp miễn giảm học phí.
                    </p>
                  </div>
                  <div className="mt-6 pt-3 border-t border-slate-800/80 text-xs font-mono text-purple-400 font-bold">
                    &bull; Hậu quả: Thất thoát an ninh, sai lệch cơ sở pháp lý đại học
                  </div>
                </FloatingCard>
              </div>
            </div>
          )}

          {/* PHASE 3: The Solution - Academic Chatbot Service (38.2s - End / frames 1145 - 1305) */}
          {frame >= 1145 && (
            <div style={{ opacity: phase3Opacity }} className="w-full max-w-[1500px] flex flex-col items-center">
              <FloatingCard delay={0} floatOffset={0} className="w-full bg-gradient-to-r from-blue-950/70 via-slate-900/95 to-cyan-950/70 border-2 border-cyan-400/80 rounded-3xl p-10 shadow-2xl shadow-cyan-500/15 flex items-center gap-10">
                <div className="w-24 h-24 rounded-3xl bg-cyan-500/20 text-cyan-300 flex items-center justify-center border-2 border-cyan-400/50 shrink-0 shadow-lg shadow-cyan-500/20">
                  <Bot size={54} />
                </div>
                <div className="flex-1">
                  <div className="inline-block px-3.5 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-mono font-bold border border-cyan-500/40 mb-3">
                    GIẢI PHÁP SẢN XUẤT CHÍNH THỨC
                  </div>
                  <h3 className="text-3xl font-black text-white">
                    IUH Academic Chatbot Service
                  </h3>
                  <p className="text-base text-slate-200 mt-3 leading-relaxed">
                    Được thiết kế chuyên sâu để giải quyết triệt để 3 tử huyệt trên, kết hợp kiến trúc <strong>Advanced RAG</strong> có kiểm soát, phân cấp <strong>Parent-Child</strong>, bộ nhớ đệm ngữ nghĩa an toàn và <strong>Context Sandboxing</strong> tuyệt đối.
                  </p>
                  <div className="grid grid-cols-3 gap-4 mt-6 pt-5 border-t border-slate-800/80 text-xs font-mono">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold">
                      <CheckCircle2 size={16} /> Bảo toàn cấu trúc bảng biểu
                    </div>
                    <div className="flex items-center gap-2 text-cyan-400 font-bold">
                      <CheckCircle2 size={16} /> Triệt tiêu xung đột niên khóa
                    </div>
                    <div className="flex items-center gap-2 text-purple-400 font-bold">
                      <CheckCircle2 size={16} /> Cách ly tiêm mã 100%
                    </div>
                  </div>
                </div>
              </FloatingCard>
            </div>
          )}

        </div>

      </SceneMotionWrapper>
    </div>
  );
};
