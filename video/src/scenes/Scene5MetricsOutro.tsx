import React from 'react';
import { Audio, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Award, CheckCircle2, Flame, Shield, TrendingUp, Zap } from 'lucide-react';
import { SubtitlesBar } from '../components/SubtitlesBar';

export const Scene5MetricsOutro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  // Dynamic Subtitles progression (1008 frames total = ~33.6s)
  let subText = 'Nhờ những cải tiến kỹ thuật đồng bộ, hệ thống đã vượt qua toàn bộ 126 bài kiểm thử tự động với tỷ lệ chính xác tuyệt đối 100%.';
  if (frame >= 350 && frame < 700) {
    subText = 'Thời gian phản hồi khi trúng bộ đệm chỉ dưới 20ms, độ chính xác truy xuất tăng hơn 25%, và tiết kiệm gần 500 token trên mỗi câu hỏi.';
  } else if (frame >= 700) {
    subText = 'Hệ sinh thái AI Microservices là một giải pháp hoàn chỉnh, an toàn và sẵn sàng phục vụ thực tế cho sinh viên IUH. Xin trân trọng cảm ơn!';
  }

  const METRICS = [
    {
      value: '126 / 126',
      label: 'Unit Tests Passed',
      desc: '100% Pass Rate trên 7 test suites',
      icon: CheckCircle2,
      color: '#10b981',
      bg: 'rgba(16, 185, 129, 0.12)',
    },
    {
      value: '< 20ms',
      label: 'Semantic Cache Hit',
      desc: 'Phản hồi tức thì với Cross-Encoder verify',
      icon: Zap,
      color: '#ef4444',
      bg: 'rgba(239, 68, 68, 0.12)',
    },
    {
      value: '-64%',
      label: 'Token Prompt Reduction',
      desc: 'Tiết kiệm ~500 tokens/lượt hỏi quy chế',
      icon: TrendingUp,
      color: '#f59e0b',
      bg: 'rgba(245, 158, 11, 0.12)',
    },
    {
      value: '+25%',
      label: 'MRR & Hit Rate@K',
      desc: '2-Stage Hybrid RRF vs Naive Search',
      icon: Award,
      color: '#6366f1',
      bg: 'rgba(99, 102, 241, 0.12)',
    },
    {
      value: '100%',
      label: 'Layout Preservation',
      desc: 'Bảo toàn công thức LaTeX & bảng Markdown',
      icon: Flame,
      color: '#8b5cf6',
      bg: 'rgba(139, 92, 246, 0.12)',
    },
    {
      value: 'Multi-layer',
      label: 'AI Guardrails Active',
      desc: 'Chặn Prompt Injection & Special Tokens',
      icon: Shield,
      color: '#06b6d4',
      bg: 'rgba(6, 182, 212, 0.12)',
    },
  ];

  return (
    <div className="relative w-full h-full bg-slate-950 text-white flex flex-col items-center justify-center p-16 font-sans overflow-hidden select-none">
      {/* Audio Voiceover: VieNeu-TTS Studio Quality */}
      <Audio src={staticFile('audio/scene5.mp3')} volume={1} />

      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[550px] bg-gradient-to-tr from-emerald-900/25 via-indigo-900/20 to-cyan-900/25 blur-[160px] rounded-full" />

      {/* Title */}
      <div style={{ transform: `scale(${titleScale})` }} className="text-center mb-10">
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950/70 border border-emerald-800/80 px-3.5 py-1 rounded-full mb-3 inline-block">
          Production Quality Gates &amp; Benchmark Results
        </span>
        <h2 className="text-4xl font-extrabold text-slate-100 tracking-tight mt-1">
          Số Liệu Đo Lường &amp; Hiệu Năng Vượt Trội
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto mt-2">
          Hệ thống sẵn sàng vận hành thực tế tại Đại học Công nghiệp TP. Hồ Chí Minh
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-6 max-w-5xl w-full">
        {METRICS.map((metric, idx) => {
          const itemProgress = spring({
            frame: frame - 15 - idx * 5,
            fps,
          });

          const Icon = metric.icon;

          return (
            <div
              key={idx}
              style={{
                opacity: itemProgress,
                transform: `scale(${itemProgress})`,
                backgroundColor: metric.bg,
                borderColor: `${metric.color}55`,
              }}
              className="border rounded-2xl p-6 backdrop-blur-xl flex flex-col justify-between shadow-xl"
            >
              <div className="flex items-center justify-between mb-4">
                <span
                  className="p-3 rounded-xl text-white"
                  style={{ backgroundColor: metric.color }}
                >
                  <Icon size={22} />
                </span>
                <span
                  className="text-3xl font-black tracking-tight"
                  style={{ color: metric.color }}
                >
                  {metric.value}
                </span>
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-100 mb-1">
                  {metric.label}
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {metric.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Synchronized Subtitles Bar */}
      <SubtitlesBar text={subText} />
    </div>
  );
};
