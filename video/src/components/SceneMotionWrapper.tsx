import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

interface SceneMotionWrapperProps {
  children: React.ReactNode;
  durationInFrames: number;
  className?: string;
}

export const SceneMotionWrapper: React.FC<SceneMotionWrapperProps> = ({
  children,
  durationInFrames,
  className = '',
}) => {
  const frame = useCurrentFrame();

  // Completely stationary scene wrapper: zero camera pans, zero zoom, zero shaking
  const transitionFrames = 12;
  const enterOpacity = interpolate(frame, [0, transitionFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const exitOpacity = interpolate(
    frame,
    [durationInFrames - transitionFrames, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const opacity = Math.min(enterOpacity, exitOpacity);

  return (
    <div
      className={`relative w-full h-full overflow-hidden ${className}`}
      style={{
        opacity,
      }}
    >
      {children}
    </div>
  );
};
