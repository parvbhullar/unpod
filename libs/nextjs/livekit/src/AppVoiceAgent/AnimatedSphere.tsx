import React, { useEffect, useRef, useState } from 'react';
import styled, { keyframes } from 'styled-components';

// Linear rotation - continuous without reset (1000 rotations)
const rotate = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360000deg); // 1000 full rotations
  }
`;

// Counter rotation for second wave layer
const rotateReverse = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(-252000deg); // 0.7 * 360000
  }
`;

// Subtle pulse - smoother with easing (~2.6 seconds per cycle at 1.15x speed)
const pulse = keyframes`
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
`;

// Slow clockwise circular movement for highlight - kept on front
const moveCircular = keyframes`
  0% {
    transform: translate(0, 0);
  }
  25% {
    transform: translate(8px, 5px);
  }
  50% {
    transform: translate(5px, 10px);
  }
  75% {
    transform: translate(-3px, 5px);
  }
  100% {
    transform: translate(0, 0);
  }
`;

const SphereContainer = styled.div<{ size: number }>`
  position: relative;
  width: ${({ size }) => size}px;
  height: ${({ size }) => size}px;
  display: flex;
  align-items: center;
  justify-content: center;
  transform-style: preserve-3d;
  -webkit-transform-style: preserve-3d;
`;

// Background glow layer 1 - larger
const GlowLayer1 = styled.div<{ size: number; $isReady?: boolean }>`
  position: absolute;
  width: ${({ size }) => size}px;
  height: ${({ size }) => size}px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(208, 204, 255, 0.3) 0%,
    rgba(244, 201, 255, 0.1) 50%,
    transparent 100%
  );
  animation: ${pulse} 2.6s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  animation-play-state: ${({ $isReady }) => ($isReady ? 'running' : 'paused')};
  will-change: transform;
  backface-visibility: hidden;
  perspective: 1000px;
`;

// Background glow layer 2 - smaller
const GlowLayer2 = styled.div<{ size: number; $isReady?: boolean }>`
  position: absolute;
  width: ${({ size }) => size * 0.9}px;
  height: ${({ size }) => size * 0.9}px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(180, 176, 255, 0.2) 30%,
    transparent 100%
  );
  animation: ${pulse} 2.6s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  animation-play-state: ${({ $isReady }) => ($isReady ? 'running' : 'paused')};
  will-change: transform;
  backface-visibility: hidden;
  perspective: 1000px;
`;

// Main sphere base
const SphereBase = styled.div<{ size: number }>`
  position: absolute;
  width: ${({ size }) => size * 0.75}px;
  height: ${({ size }) => size * 0.75}px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f0f0ff 0%, #e8e4ff 50%, #ded8ff 100%);
  box-shadow: 0 0 30px 10px rgba(208, 204, 255, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
`;

// Static wrapper for initial angle offset
const WaveLayerWrapper = styled.div<{ size: number; $initialAngle?: number }>`
  position: absolute;
  width: ${({ size }) => size}px;
  height: ${({ size }) => size}px;
  transform: rotate(${({ $initialAngle }) => $initialAngle || 0}deg);
  transform-origin: center center;
`;

// Animated wrapper for rotation
const WaveLayerAnimated = styled.div<{ reverse?: boolean; $isReady?: boolean }>`
  position: absolute;
  width: 100%;
  height: 100%;
  animation: ${({ reverse }) => (reverse ? rotateReverse : rotate)} 17390s
    linear infinite;
  animation-play-state: ${({ $isReady }) => ($isReady ? 'running' : 'paused')};
  will-change: transform;
  transform-origin: center center;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  -webkit-transform-style: preserve-3d;
  transform-style: preserve-3d;
`;

// Pulse wrapper (separate from rotation to prevent conflicts)
const WaveLayerPulse = styled.div<{ $isReady?: boolean }>`
  position: absolute;
  width: 100%;
  height: 100%;
  animation: ${pulse} 2.6s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  animation-play-state: ${({ $isReady }) => ($isReady ? 'running' : 'paused')};
  will-change: transform;
  transform-origin: center center;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  -webkit-transform-style: preserve-3d;
  transform-style: preserve-3d;
`;

// Center highlight
const CenterHighlight = styled.div<{ size: number }>`
  position: absolute;
  width: ${({ size }) => size * 0.35}px;
  height: ${({ size }) => size * 0.35}px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.8) 0%,
    rgba(255, 255, 255, 0.3) 40%,
    transparent 100%
  );
  pointer-events: none;
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
`;

// Top highlight shine
const TopHighlight = styled.div<{ size: number }>`
  position: absolute;
  top: ${({ size }) => size * 0.15}px;
  left: ${({ size }) => size * 0.3}px;
  width: ${({ size }) => size * 0.2}px;
  height: ${({ size }) => size * 0.15}px;
  border-radius: 100px;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.6) 0%,
    rgba(255, 255, 255, 0) 100%
  );
  pointer-events: none;
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: ${moveCircular} 8s ease-in-out infinite;
  will-change: transform;
`;

type AnimatedSphereBreakpoints = {
  mobile?: number;
  tablet?: number;
  desktop?: number;};

type AnimatedSphereProps = {
  size?: number;
  breakpoints?: AnimatedSphereBreakpoints;};

/**
 * AnimatedSphere Component
 * A beautiful pulsing sphere with rotating wavy layers
 * Recreates the Flutter AnimatedSphere design with enhanced smoothness
 *
 * Architecture:
 * - Nested wrapper structure prevents transform conflicts and jerking
 * - Each wave layer has 3 wrappers:
 *   1. WaveLayerWrapper - Static initial angle offset (15°/30°)
 *   2. WaveLayerAnimated - Rotation animation (separate layer)
 *   3. WaveLayerPulse - Pulse animation (separate layer)
 * - GPU acceleration via backface-visibility and preserve-3d
 * - 240 canvas segments for ultra-smooth wavy curves
 * - 1.15x speed for more dynamic feel
 *
 * @param {Object} props - Component properties
 * @param {number} props.size - Size of the sphere (default: 250)
 * @param {Object} props.breakpoints - Responsive sizes { mobile: 60, tablet: 120, desktop: 250 }
 */
export const AnimatedSphere: React.FC<AnimatedSphereProps> = ({
  size = 250,
  breakpoints,
}) => {
  // Calculate responsive size based on breakpoints
  const [responsiveSize, setResponsiveSize] = useState(size);

  useEffect(() => {
    if (!breakpoints) return;

    const updateSize = () => {
      const width = window.innerWidth;
      if (breakpoints.mobile && width < 768) {
        setResponsiveSize(breakpoints.mobile);
      } else if (breakpoints.tablet && width >= 768 && width < 1024) {
        setResponsiveSize(breakpoints.tablet);
      } else if (breakpoints.desktop && width >= 1024) {
        setResponsiveSize(breakpoints.desktop);
      } else {
        setResponsiveSize(size);
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [breakpoints, size]);

  const currentSize = breakpoints ? responsiveSize : size;
  const waveCanvas1Ref = useRef<HTMLCanvasElement | null>(null);
  const waveCanvas2Ref = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const canvas1 = waveCanvas1Ref.current;
    const canvas2 = waveCanvas2Ref.current;
    if (!canvas1 || !canvas2) return;

    const ctx1 = canvas1.getContext('2d');
    const ctx2 = canvas2.getContext('2d');
    if (!ctx1 || !ctx2) return;

    const waveSize1 = currentSize * 0.6;
    const waveSize2 = currentSize * 0.55;

    // Set canvas size with device pixel ratio for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    canvas1.width = waveSize1 * dpr;
    canvas1.height = waveSize1 * dpr;
    canvas2.width = waveSize2 * dpr;
    canvas2.height = waveSize2 * dpr;

    ctx1.scale(dpr, dpr);
    ctx2.scale(dpr, dpr);

    const drawWave = (
      ctx: CanvasRenderingContext2D,
      size: number,
      color: string,
      thickness: number,
      offset: number,
    ) => {
      ctx.clearRect(0, 0, size, size);

      const centerX = size / 2;
      const centerY = size / 2;
      const radius = size / 2 - thickness / 2;

      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = thickness;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      // Enable smoothing for better quality
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';

      // Create ultra-smooth wavy path (240 segments for even smoother curves)
      const segments = 240;

      for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const angle = t * 2 * Math.PI;

        // Smooth continuous wave using multiple harmonics
        const wave1 = Math.sin(angle * 3 + offset) * 5;
        const wave2 = Math.sin(angle * 5 - offset * 0.7) * 2;
        const waveOffset = wave1 + wave2;

        const r = radius + waveOffset;
        const x = centerX + Math.cos(angle) * r;
        const y = centerY + Math.sin(angle) * r;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.closePath();
      ctx.stroke();
    };

    const animate = () => {
      if (!startTimeRef.current) {
        startTimeRef.current = Date.now();
        // Signal that animations are ready to start
        setIsReady(true);
      }

      const elapsed = (Date.now() - startTimeRef.current) / 1000; // seconds

      // Continuous orbit offset - no reset, seamless loop
      // 7.5π over 52.17 seconds = ~0.4519 radians per second
      const orbit = elapsed * ((7.5 * Math.PI) / 52.17);

      // Draw wave layers with orbit offset and smoother rendering
      drawWave(ctx1, waveSize1, 'rgba(155, 143, 255, 0.35)', 35, orbit);
      drawWave(ctx2, waveSize2, 'rgba(123, 168, 255, 0.35)', 30, -orbit * 1.1);

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [currentSize]);

  return (
    <SphereContainer size={currentSize} style={{ opacity: isReady ? 1 : 0 }}>
      {/* Background glow layer 1 */}
      <GlowLayer1 size={currentSize} $isReady={isReady} />

      {/* Background glow layer 2 */}
      <GlowLayer2 size={currentSize} $isReady={isReady} />

      {/* Main sphere base */}
      <SphereBase size={currentSize} />

      {/* Rotating wave layer 1 (Purple) - 15° initial angle */}
      <WaveLayerWrapper size={currentSize * 0.6} $initialAngle={15}>
        <WaveLayerAnimated reverse={false} $isReady={isReady}>
          <WaveLayerPulse $isReady={isReady}>
            <canvas
              ref={waveCanvas1Ref}
              style={{
                width: '100%',
                height: '100%',
                display: 'block',
              }}
            />
          </WaveLayerPulse>
        </WaveLayerAnimated>
      </WaveLayerWrapper>

      {/* Rotating wave layer 2 (Blue-Purple) - 30° initial angle (15° offset from first) */}
      <WaveLayerWrapper size={currentSize * 0.55} $initialAngle={30}>
        <WaveLayerAnimated reverse={true} $isReady={isReady}>
          <WaveLayerPulse $isReady={isReady}>
            <canvas
              ref={waveCanvas2Ref}
              style={{
                width: '100%',
                height: '100%',
                display: 'block',
              }}
            />
          </WaveLayerPulse>
        </WaveLayerAnimated>
      </WaveLayerWrapper>

      {/* Center highlight */}
      <CenterHighlight size={currentSize} />

      {/* Top highlight shine */}
      <TopHighlight size={currentSize} />
    </SphereContainer>
  );
};

export default AnimatedSphere;
