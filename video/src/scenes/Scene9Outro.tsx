import React from 'react';
import { Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Check, CheckCircle2, Cpu, GitMerge, GraduationCap, HeartHandshake, Layers, ShieldCheck, Zap, Activity, Sparkles } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';

export const Scene9Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Active highlights based on exact sentenceTimings.json:
  // Sentence 0 (frames 0 - 205): System synthesis & Building E intro
  // Sentence 1 (frames 213 - 656): 4 Golden Metrics Banner
  // Sentence 2 (frames 664 - 865): Faculty & Students Perspective Card
  // Sentence 3 (frames 873 - 1150): AI Engineers Perspective Card
  // Sentence 4 (frames 1158 - 1205): Thank You Badge
  const isMetricsActive = frame >= 210 && frame < 660;
  const isFacultyActive = frame >= 660 && frame < 870;
  const isEngineerActive = frame >= 870 && frame < 1155;
  const isThankYouActive = frame >= 1155;

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene9.mp3')} volume={1} />
      <AnimatedBackground theme="cyan" />

      <SceneMotionWrapper durationInFrames={1213} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        {/* Compact Integrated Header Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <GraduationCap size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-cyan-400">
                  INDUSTRIAL UNIVERSITY OF HO CHI MINH CITY
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; IUH ACADEMIC COUNSELING CHATBOT SERVICE</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                TỔNG KẾT &amp; TẦM NHÌN HỆ THỐNG
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono bg-emerald-500/20 text-emerald-300 font-black px-4 py-1.5 rounded-full border border-emerald-500/40 flex items-center gap-2 shadow-lg shadow-emerald-500/15">
              <CheckCircle2 size={16} /> PRODUCTION READY &bull; 100% RELIABLE
            </span>
          </div>
        </div>

        {/* Main Content Area: Campus Photo & Dual Perspectives (Fills ~75% screen) */}
        <div className="flex-1 grid grid-cols-12 gap-7 my-auto items-stretch w-full max-w-[1780px] mx-auto py-2">
          
          {/* Left Column: Campus Image Shot & Live Metrics (5 cols) */}
          <div className="col-span-5 flex flex-col gap-4 justify-between h-full">
            <FloatingCard delay={0} floatOffset={0} className="relative overflow-hidden rounded-3xl border-2 border-slate-700/80 shadow-2xl bg-slate-900 group flex-1 flex flex-col justify-end">
              <Img
                src={staticFile('images/anh-nha-E-iuh.jpg')}
                className="w-full h-full min-h-[460px] object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
              
              <div className="absolute bottom-6 left-6 right-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-3 py-1 bg-blue-600 text-xs font-bold rounded-lg font-mono uppercase tracking-wider text-white">
                    Nhà E &bull; Trụ sở chính IUH
                  </span>
                  <span className="text-xs text-slate-300 font-mono">Phòng Quản lý Đào tạo</span>
                </div>
                <h3 className="text-2xl font-black text-white drop-shadow-md">
                  Trường Đại học Công nghiệp TP.HCM
                </h3>
                <p className="text-sm text-slate-200 drop-shadow mt-1">
                  Số 12 Nguyễn Văn Bảo, Phường 4, Quận Gò Vấp, TP.HCM
                </p>
              </div>
            </FloatingCard>

            {/* 4 Golden Metrics Banner */}
            <FloatingCard
              delay={6}
              floatOffset={1}
              className={`p-4 rounded-3xl flex flex-col gap-2.5 transition-colors duration-300 border-2 ${
                isMetricsActive
                  ? 'bg-slate-900/95 border-cyan-400 shadow-2xl shadow-cyan-500/25'
                  : 'bg-slate-900/95 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-3.5 h-3.5 rounded-full bg-emerald-400" />
                  <span className="text-xs font-mono text-slate-100 font-bold">4 Chỉ Số Vàng Đạt Được Trong Thực Tế:</span>
                </div>
                <span className="text-xs font-mono px-3 py-1 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-bold">Production Verified</span>
              </div>
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-800 font-mono text-xs text-center">
                <div className="p-2 rounded-xl bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Unit Tests</span>
                  <span className="text-emerald-400 font-bold">126/126 Pass</span>
                </div>
                <div className="p-2 rounded-xl bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Redis Cache</span>
                  <span className="text-cyan-400 font-bold">12ms Response</span>
                </div>
                <div className="p-2 rounded-xl bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Ảo giác quy chế</span>
                  <span className="text-emerald-400 font-bold">0.0% Gate</span>
                </div>
                <div className="p-2 rounded-xl bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-400 block text-[10px]">Tiết kiệm token</span>
                  <span className="text-amber-400 font-bold">-60% Cost</span>
                </div>
              </div>
            </FloatingCard>
          </div>

          {/* Right Column: Dual Perspectives Cards (7 cols) */}
          <div className="col-span-7 flex flex-col gap-4 justify-between h-full">
            
            {/* Faculty & Students Card */}
            <FloatingCard
              delay={8}
              floatOffset={2}
              className={`rounded-3xl p-6 shadow-2xl flex-1 flex flex-col justify-between transition-colors duration-300 border-2 ${
                isFacultyActive
                  ? 'bg-gradient-to-r from-blue-950/80 via-slate-900/95 to-slate-900 border-blue-400 shadow-2xl shadow-blue-500/25'
                  : 'bg-gradient-to-r from-blue-950/40 via-slate-900/90 to-slate-900 border-slate-800'
              }`}
            >
              <div>
                <div className="flex items-center gap-3.5 mb-2.5 pb-2 border-b border-slate-800">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/25 text-blue-300 flex items-center justify-center border border-blue-500/40 shrink-0">
                    <HeartHandshake size={26} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Lăng Kính Nghiệp Vụ (Giảng Viên &amp; Sinh Viên)</h3>
                    <span className="text-xs text-blue-300 font-mono font-bold">Trợ lý học vụ số 100% trung thực, tin cậy</span>
                  </div>
                </div>
                <ul className="text-sm text-slate-200 space-y-2.5 mt-3 leading-relaxed">
                  <li className="flex items-start gap-3">
                    <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                    <span><strong>Không ảo giác, không nói dối:</strong> Mọi câu trả lời đều neo trực tiếp vào văn bản quy chế chính thức của Trường Đại học Công nghiệp TP.HCM, trích dẫn rõ Điều, Khoản và Phụ lục.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                    <span><strong>Chính xác theo từng khóa học:</strong> Phân biệt rạch ròi quy chế đào tạo và mức thu học phí giữa sinh viên các khóa K19, K20, K21, triệt tiêu nguy cơ áp dụng nhầm văn bản cũ.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                    <span><strong>Phản hồi tức thì:</strong> Phục vụ 24/7 hàng nghìn sinh viên cùng lúc trong mùa cao điểm đăng ký môn học và đóng học phí, giải tỏa áp lực trực tiếp cho cán bộ Phòng Đào tạo.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                    <span><strong>Minh bạch và có thể kiểm chứng:</strong> Cung cấp đầy đủ đường dẫn và trích lục nguyên văn để sinh viên đối chiếu trực tiếp với sổ tay người học chính thức.</span>
                  </li>
                </ul>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-800 text-xs font-mono text-cyan-300 font-bold flex items-center justify-between">
                <span>Bảo vệ quyền lợi học tập của sinh viên IUH tuyệt đối</span>
                <span className="text-emerald-400 font-bold">Độ tin cậy nghiệp vụ: 100%</span>
              </div>
            </FloatingCard>

            {/* AI Engineers Card */}
            <FloatingCard
              delay={14}
              floatOffset={3}
              className={`rounded-3xl p-6 shadow-2xl flex-1 flex flex-col justify-between transition-colors duration-300 border-2 ${
                isEngineerActive
                  ? 'bg-gradient-to-r from-emerald-950/80 via-slate-900/95 to-slate-900 border-emerald-400 shadow-2xl shadow-emerald-500/25'
                  : 'bg-gradient-to-r from-emerald-950/40 via-slate-900/90 to-slate-900 border-slate-800'
              }`}
            >
              <div>
                <div className="flex items-center gap-3.5 mb-2.5 pb-2 border-b border-slate-800">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-500/25 text-emerald-300 flex items-center justify-center border border-emerald-500/40 shrink-0">
                    <Cpu size={26} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Lăng Kính Kỹ Thuật (Kỹ Sư AI Chuyên Nghiệp)</h3>
                    <span className="text-xs text-emerald-300 font-mono font-bold">Kết tinh các nghiên cứu khoa học tiên tiến</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-2.5 font-mono text-xs">
                  <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-slate-200 flex flex-col justify-between">
                    <div>
                      <strong className="text-emerald-300 block mb-1 flex items-center gap-1.5"><Layers size={15} /> Hybrid Chunking:</strong>
                      Table-Aware nhân bản header bảng &amp; 1.445 Parent Chunks + 3.252 Child Chunks gối đầu.
                    </div>
                    <div className="text-[10px] text-cyan-400 mt-2 font-mono">&bull; Vector 768d &bull; HNSW Cosine</div>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-slate-200 flex flex-col justify-between">
                    <div>
                      <strong className="text-emerald-300 block mb-1 flex items-center gap-1.5"><Zap size={15} /> 2-Stage Cache:</strong>
                      Redis O(1) 12ms + pgvector 768d và Entity Numbers Guard chống nhầm năm học.
                    </div>
                    <div className="text-[10px] text-amber-400 mt-2 font-mono">&bull; Latency 12ms &bull; Zero False Positives</div>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-slate-200 flex flex-col justify-between">
                    <div>
                      <strong className="text-emerald-300 block mb-1 flex items-center gap-1.5"><GitMerge size={15} /> Hybrid RRF (k=60):</strong>
                      Dense 768d + Sparse BM25 kết hợp BGE-Reranker-v2-m3 chấm điểm chéo sâu.
                    </div>
                    <div className="text-[10px] text-blue-400 mt-2 font-mono">&bull; k=60 &bull; Quota 2-8 Parent Chunks</div>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-slate-200 flex flex-col justify-between">
                    <div>
                      <strong className="text-emerald-300 block mb-1 flex items-center gap-1.5"><ShieldCheck size={15} /> Sandboxing &amp; CoT:</strong>
                      Sandwich Reorder trị Lost-in-the-Middle + XML cách ly chống Prompt Injection.
                    </div>
                    <div className="text-[10px] text-purple-400 mt-2 font-mono">&bull; U-Curve [#1,#3,#5,#4,#2] &bull; -60% Tokens</div>
                  </div>
                </div>
              </div>

              <div className="mt-2.5 pt-2 border-t border-slate-800 text-xs font-mono text-emerald-300 font-bold flex items-center justify-between">
                <span>Kiến trúc RAG thế hệ mới chuyên sâu cho dữ liệu pháp lý &amp; học vụ</span>
                <span className="text-cyan-300 font-bold">126/126 Tests Passed (100%)</span>
              </div>
            </FloatingCard>

            {/* Final Thank You Badge */}
            {isThankYouActive && (
              <div className="p-3 bg-gradient-to-r from-cyan-950/80 via-blue-900/90 to-purple-950/80 border-2 border-cyan-400 rounded-2xl flex items-center justify-center gap-3 text-white font-bold text-center shadow-2xl">
                <Sparkles size={20} className="text-amber-300" />
                <span className="text-sm uppercase tracking-wider font-mono">
                  Xin Trân Trọng Cảm Ơn Quý Thầy Cô &amp; Các Bạn Đã Theo Dõi!
                </span>
                <Sparkles size={20} className="text-amber-300" />
              </div>
            )}

          </div>

        </div>
      </SceneMotionWrapper>
    </div>
  );
};
