import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { Volume2 } from 'lucide-react';

interface Props {
  text: string;
}

export const SubtitlesBar: React.FC<Props> = ({ text }) => {
  const frame = useCurrentFrame();

  // Subtle wave bar animation for visual feedback of active voice
  const bar1 = interpolate(Math.sin(frame / 4), [-1, 1], [6, 22]);
  const bar2 = interpolate(Math.cos(frame / 3), [-1, 1], [8, 26]);
  const bar3 = interpolate(Math.sin(frame / 5), [-1, 1], [7, 24]);
  const bar4 = interpolate(Math.cos(frame / 4), [-1, 1], [5, 20]);

  // Gentle float for subtitle pill
  const floatY = Math.sin(frame * 0.04) * 3;

  return (
    <div
      className="absolute bottom-7 left-1/2 -translate-x-1/2 z-50 max-w-5xl w-full px-6 pointer-events-none"
      style={{ transform: `translate(-50%, ${floatY}px)` }}
    >
      <div className="bg-slate-950/95 border-2 border-slate-700/80 rounded-2xl px-6 py-4 backdrop-blur-2xl shadow-[0_12px_40px_rgba(0,0,0,0.85)] flex items-center gap-5">
        {/* Animated Voice Equalizer */}
        <div className="flex items-center gap-2 shrink-0 p-2.5 rounded-xl bg-cyan-950/70 border border-cyan-800/80 text-cyan-400">
          <Volume2 size={20} className="text-cyan-400" />
          <div className="flex items-end gap-1 h-6 w-9">
            <span
              style={{ height: `${bar1}px` }}
              className="w-1.5 bg-cyan-400 rounded-full"
            />
            <span
              style={{ height: `${bar2}px` }}
              className="w-1.5 bg-blue-400 rounded-full"
            />
            <span
              style={{ height: `${bar3}px` }}
              className="w-1.5 bg-purple-400 rounded-full"
            />
            <span
              style={{ height: `${bar4}px` }}
              className="w-1.5 bg-emerald-400 rounded-full"
            />
          </div>
        </div>

        {/* Subtitle Voiceover Text - Large, Bold & Ultra Readable */}
        <p className="text-base md:text-lg font-bold text-white leading-relaxed drop-shadow-md tracking-wide">
          {text}
        </p>
      </div>
    </div>
  );
};
