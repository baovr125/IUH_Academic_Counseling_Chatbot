import React from 'react';

interface AnimatedBackgroundProps {
  theme?: 'blue' | 'purple' | 'emerald' | 'amber' | 'slate' | 'cyan';
}

export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({ theme = 'blue' }) => {
  // Completely stationary, calm, dark architectural background
  const getGlowColors = () => {
    switch (theme) {
      case 'purple':
        return {
          glow1: 'from-purple-900/20 via-indigo-950/15 to-transparent',
          glow2: 'from-blue-900/15 via-slate-900/10 to-transparent',
        };
      case 'emerald':
        return {
          glow1: 'from-emerald-900/20 via-teal-950/15 to-transparent',
          glow2: 'from-cyan-900/15 via-slate-900/10 to-transparent',
        };
      case 'amber':
        return {
          glow1: 'from-amber-900/15 via-orange-950/10 to-transparent',
          glow2: 'from-blue-900/15 via-slate-900/10 to-transparent',
        };
      case 'cyan':
        return {
          glow1: 'from-cyan-900/20 via-blue-950/15 to-transparent',
          glow2: 'from-indigo-900/15 via-slate-900/10 to-transparent',
        };
      default:
        return {
          glow1: 'from-blue-900/20 via-indigo-950/15 to-transparent',
          glow2: 'from-cyan-900/15 via-slate-900/10 to-transparent',
        };
    }
  };

  const { glow1, glow2 } = getGlowColors();

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0">
      {/* Deep Space Base */}
      <div className="absolute inset-0 bg-slate-950" />

      {/* Static Soft Ambient Glow Orbs */}
      <div
        className={`absolute top-[-100px] left-1/4 w-[800px] h-[600px] bg-gradient-to-br ${glow1} blur-[160px] rounded-full`}
      />
      <div
        className={`absolute bottom-[-100px] right-1/4 w-[800px] h-[600px] bg-gradient-to-tl ${glow2} blur-[180px] rounded-full`}
      />

      {/* Crisp Static Subtle Tech Grid */}
      <div
        className="absolute inset-0 opacity-[0.10]"
        style={{
          backgroundImage: 'radial-gradient(circle at 1.5px 1.5px, rgba(255, 255, 255, 0.4) 1.5px, transparent 0)',
          backgroundSize: '40px 40px',
        }}
      />
    </div>
  );
};
