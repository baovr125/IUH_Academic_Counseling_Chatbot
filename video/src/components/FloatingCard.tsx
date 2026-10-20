import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

interface FloatingCardProps {
  children: React.ReactNode;
  delay?: number;
  floatOffset?: number;
  className?: string;
  style?: React.CSSProperties;
  scaleEntrance?: boolean;
}

export const FloatingCard: React.FC<FloatingCardProps> = ({
  children,
  delay = 0,
  className = '',
  style = {},
}) => {
  const frame = useCurrentFrame();

  // Completely stationary card with calm, gentle fade-in (zero movement, zero floating)
  const opacity = delay > 0 
    ? interpolate(frame, [delay, delay + 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;

  return (
    <div
      className={className}
      style={{
        ...style,
        opacity,
      }}
    >
      {children}
    </div>
  );
};
