import React from 'react';
import { Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Activity, AlertOctagon, Check, CheckCircle2, Cpu, Database, Layers, Network, ShieldCheck, Zap } from 'lucide-react';
import { AnimatedBackground } from '../components/AnimatedBackground';
import { FloatingCard } from '../components/FloatingCard';
import { SceneMotionWrapper } from '../components/SceneMotionWrapper';
import { SystemArchitectureDiagram } from '../components/SystemArchitectureDiagram';
import { EndToEndRAGFlowDiagram } from '../components/EndToEndRAGFlowDiagram';

export const Scene2ArchitectureComparison: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase transitions across 1863 frames (~62.1 seconds) calibrated to exact audio sentences:
  // Phase 1: Canonical 3-Column Diagram (frames 0 to 325)
  // Phase 2: Engineering Trade-off (frames 320 to 755)
  // Phase 3: End-to-End RAG Flow Diagram with Dynamic Step Highlights (frames 750 to 1863)
  const phase1Opacity = interpolate(frame, [0, 20, 310, 325], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const phase2Opacity = interpolate(frame, [320, 340, 740, 755], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const phase3Opacity = interpolate(frame, [750, 770], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Latency meter animation in Phase 2
  const modularLatency = interpolate(frame, [350, 680], [1.2, 8.5], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col font-sans overflow-hidden select-none">
      <Audio src={staticFile('audio/scene2.mp3')} volume={1} />
      <AnimatedBackground theme="purple" />

      <SceneMotionWrapper durationInFrames={2360} className="flex flex-col w-full h-full px-8 py-5 justify-between">
        {/* Strictly Single Main Scene Title Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <Layers size={22} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold tracking-wider text-blue-400">
                  SCIENTIFIC RAG FOUNDATION
                </span>
                <span className="text-xs font-mono text-slate-500">&bull; GAO ET AL. (2023) SURVEY</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white">
                CƠ SỞ KHOA HỌC: ADVANCED RAG HAY MODULAR RAG?
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono bg-emerald-500/15 text-emerald-400 font-bold px-3.5 py-1.5 rounded-full border border-emerald-500/30 flex items-center gap-1.5">
              <CheckCircle2 size={15} /> Production Engineering Choice
            </span>
          </div>
        </div>

        {/* Main Content Area (Occupies ~72% useful screen area) */}
        <div className="flex-1 flex flex-col justify-center items-center my-auto w-full">
          
          {/* PHASE 1: The Canonical 3-Column Diagram (0 - 10.7s / frames 0 - 325) */}
          {frame < 330 && (
            <div style={{ opacity: phase1Opacity }} className="w-full flex items-center justify-between gap-8 px-2">
              <FloatingCard delay={0} floatOffset={0} className="w-1/2 flex flex-col items-center">
                <div className="rounded-3xl overflow-hidden border-2 border-slate-700 bg-slate-900/90 shadow-2xl p-4 w-full max-w-[760px]">
                  <Img
                    src={staticFile('images/naive-advance-modular-RAG.jpg')}
                    className="w-full h-[510px] object-contain rounded-2xl"
                  />
                  <div className="p-3 bg-slate-950/80 rounded-xl mt-3 text-center border border-slate-800">
                    <span className="text-sm font-mono text-cyan-400 font-bold">
                      Hình 1: Tiến trình phát triển 3 thế hệ kiến trúc RAG (Gao et al., 2023)
                    </span>
                  </div>
                </div>
              </FloatingCard>

              <div className="w-1/2 flex flex-col gap-4">
                <FloatingCard delay={6} floatOffset={1} className="bg-slate-900/95 border border-slate-800 rounded-3xl p-5 flex gap-5 shadow-xl">
                  <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center font-black text-slate-300 text-xl shrink-0">1</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">THẾ HỆ 1</span>
                      <span className="text-lg font-bold text-slate-200">Naive RAG (Truyền thống)</span>
                    </div>
                    <p className="text-sm text-slate-400 mt-1 leading-relaxed">
                      Quy trình tuyến tính đơn giản: Nhúng vector thô &rarr; Tìm kiếm Cosine &rarr; Đưa thẳng vào LLM. 
                      Hạn chế: độ chính xác thấp, cắt vụn ngữ cảnh, ảo giác trầm trọng.
                    </p>
                  </div>
                </FloatingCard>

                <FloatingCard delay={12} floatOffset={2} className="bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border-2 border-cyan-500/70 rounded-3xl p-5 flex gap-5 shadow-2xl shadow-cyan-500/10">
                  <div className="w-12 h-12 rounded-2xl bg-cyan-500/25 text-cyan-300 flex items-center justify-center font-black text-xl shrink-0">2</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">THẾ HỆ 2</span>
                      <span className="text-lg font-bold text-cyan-300">Advanced RAG (Xương sống IUH)</span>
                    </div>
                    <p className="text-sm text-slate-200 mt-1 leading-relaxed">
                      Bổ sung tiền xử lý Pre-retrieval (phân rã câu hỏi kép, chunking cấu trúc phân cấp) và hậu xử lý Post-retrieval (reranking, sandwich reordering). 
                      Độ trễ thấp, kiểm soát chặt chẽ, tối ưu đường truyền.
                    </p>
                  </div>
                </FloatingCard>

                <FloatingCard delay={18} floatOffset={3} className="bg-slate-900/95 border border-purple-500/50 rounded-3xl p-5 flex gap-5 shadow-xl shadow-purple-500/10">
                  <div className="w-12 h-12 rounded-2xl bg-purple-500/25 text-purple-300 flex items-center justify-center font-black text-xl shrink-0">3</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">THẾ HỆ 3</span>
                      <span className="text-lg font-bold text-purple-300">Modular RAG (Đa Module)</span>
                    </div>
                    <p className="text-sm text-slate-300 mt-1 leading-relaxed">
                      Mạng lưới các Agent/Module độc lập trao đổi qua đồ thị. Linh hoạt lý thuyết nhưng cồng kềnh thực tế, độ trễ 5-10s và nguy cơ trôi dạt trạng thái.
                    </p>
                  </div>
                </FloatingCard>
              </div>
            </div>
          )}

          {/* PHASE 2: Engineering Trade-off (10.7s - 25s / frames 320 - 755) */}
          {frame >= 320 && frame < 760 && (
            <div style={{ opacity: phase2Opacity }} className="w-full max-w-[1760px] h-[720px] flex flex-col justify-between">
              <div className="flex justify-center mb-3">
                <span className="text-xs font-mono px-4 py-1.5 rounded-full bg-rose-500/15 text-rose-300 font-bold border border-rose-500/30 uppercase tracking-wide">
                  Đánh đổi kỹ thuật: Modular RAG thuần túy vs Advanced RAG (Production)
                </span>
              </div>

              <div className="flex-1 grid grid-cols-2 gap-8 items-stretch">
                {/* Full Modular RAG Warning */}
                <FloatingCard delay={0} floatOffset={0} className="bg-slate-900/95 border-2 border-rose-500/50 rounded-3xl p-8 shadow-2xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm font-mono px-3 py-1 rounded bg-rose-500/20 text-rose-300 font-bold flex items-center gap-2">
                        <Network size={18} /> FULL MODULAR RAG THUẦN TÚY
                      </span>
                      <span className="text-xs font-mono text-rose-400 font-bold bg-rose-950/60 px-3 py-1 rounded-lg border border-rose-500/30">
                        RỦI RO CAO TRONG VẬN HÀNH
                      </span>
                    </div>

                    <div className="bg-slate-950 p-6 rounded-2xl border border-rose-900/50 mb-6">
                      <div className="flex items-center justify-between text-slate-300 text-sm mb-2">
                        <span className="font-medium">Độ trễ trung bình (Production Latency):</span>
                        <span className="text-rose-400 font-mono font-black text-4xl">{modularLatency.toFixed(1)}s</span>
                      </div>
                      <div className="w-full h-4 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-amber-500 to-rose-600 rounded-full"
                          style={{ width: `${(modularLatency / 10) * 100}%` }}
                        />
                      </div>
                      <div className="text-xs text-rose-300 mt-3 italic flex items-center gap-2">
                        <AlertOctagon size={18} /> Nguy cơ tắc nghẽn nghiêm trọng khi hàng nghìn sinh viên cùng tra cứu!
                      </div>
                    </div>

                    <ul className="text-base text-slate-300 space-y-4 leading-relaxed">
                      <li className="flex items-start gap-3">
                        <span className="text-rose-400 font-black text-xl">&bull;</span>
                        <span><strong>Đồ thị Agent phức tạp:</strong> Multi-Agent DAG chuyển đổi trạng thái liên tục làm tăng độ trễ 5 đến 10 giây mỗi câu hỏi.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-rose-400 font-black text-xl">&bull;</span>
                        <span><strong>Trôi dạt ngữ cảnh (Context Drift):</strong> Vòng lặp phản xạ đa tầng thiếu tính tất định, dễ dẫn đến ảo giác học vụ nguy hiểm.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-rose-400 font-black text-xl">&bull;</span>
                        <span><strong>Chi phí suy luận bùng nổ:</strong> Tiêu tốn số lượt gọi LLM gấp 4 lần cho mỗi lượt tư vấn thông thường.</span>
                      </li>
                    </ul>
                  </div>

                  <div className="mt-6 pt-4 border-t border-rose-900/40 text-xs font-mono text-rose-400 font-bold flex items-center justify-between">
                    <span>KHÔNG PHÙ HỢP CHO HỆ THỐNG PHỤC VỤ SỐ ĐÔNG ĐÒI HỎI ĐỘ CHÍNH XÁC CAO</span>
                    <span>&times; Rejected</span>
                  </div>
                </FloatingCard>

                {/* Advanced RAG + Selected Modules */}
                <FloatingCard delay={6} floatOffset={1} className="bg-slate-900/95 border-2 border-emerald-500/60 rounded-3xl p-8 shadow-2xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm font-mono px-3 py-1 rounded bg-emerald-500/20 text-emerald-300 font-bold flex items-center gap-2">
                        <Zap size={18} /> ADVANCED RAG + SPECIALIZED MODULES
                      </span>
                      <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-500/30">
                        LỰA CHỌN TỐI ƯU
                      </span>
                    </div>

                    <div className="bg-slate-950 p-6 rounded-2xl border border-emerald-900/50 mb-6">
                      <div className="flex items-center justify-between text-slate-300 text-sm mb-2">
                        <span className="font-medium">Độ trễ trung bình (Production Latency):</span>
                        <span className="text-emerald-400 font-mono font-black text-4xl">&lt; 1.2s</span>
                      </div>
                      <div className="w-full h-4 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: '15%' }} />
                      </div>
                      <div className="text-xs text-emerald-300 mt-3 font-mono flex items-center gap-2">
                        <CheckCircle2 size={18} /> Phản hồi gần như tức thì, độ ổn định tuyệt đối và chịu tải xuất sắc.
                      </div>
                    </div>

                    <ul className="text-base text-slate-300 space-y-4 leading-relaxed">
                      <li className="flex items-start gap-3">
                        <span className="text-emerald-400 font-black text-xl">&bull;</span>
                        <span><strong>Đường ống tất định (Deterministic Pipeline):</strong> Luồng xử lý một chiều rõ ràng: Tiền truy xuất &rarr; Truy xuất lai hợp &rarr; Hậu truy xuất.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-emerald-400 font-black text-xl">&bull;</span>
                        <span><strong>Mô hình đồng nhất:</strong> Dùng chung backend LLM cho cả Rewriter &amp; Generator qua prompt JSON Zero-shot siêu tốc.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-emerald-400 font-black text-xl">&bull;</span>
                        <span><strong>Bảo toàn cơ sở pháp lý 100%:</strong> Trích dẫn chính xác từng điều khoản quy chế, phân tách tuyệt đối theo khóa tuyển sinh.</span>
                      </li>
                    </ul>
                  </div>

                  <div className="mt-6 pt-4 border-t border-emerald-900/40 text-xs font-mono text-emerald-400 font-bold flex items-center justify-between">
                    <span>GIẢI PHÁP ĐƯỢC CHỨNG THỰC VÀ ÁP DỤNG TRONG PRODUCTION TẠI IUH</span>
                    <span className="flex items-center gap-1"><Check size={16} /> Verified</span>
                  </div>
                </FloatingCard>
              </div>
            </div>
          )}

          {/* PHASE 3: Dedicated End-to-End RAG Pipeline Diagram (25s - End / frames 750 - 1863) */}
          {frame >= 750 && (
            <div style={{ opacity: phase3Opacity }} className="w-full max-w-[1780px] h-[780px]">
              <EndToEndRAGFlowDiagram />
            </div>
          )}
        </div>
      </SceneMotionWrapper>
    </div>
  );
};
