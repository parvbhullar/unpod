'use client';

import styled, { keyframes } from 'styled-components';

// Iridescent color shift animation
const iridescentShift = keyframes`
  0% {
    background-position: 0% 50%;
    filter: hue-rotate(0deg);
  }
  50% {
    background-position: 100% 50%;
    filter: hue-rotate(20deg);
  }
  100% {
    background-position: 0% 50%;
    filter: hue-rotate(0deg);
  }
`;

// Voice pulse - core breathing animation - smoother
const voicePulse = keyframes`
  0%, 100% {
    transform: scale(1);
    opacity: 0.85;
  }
  50% {
    transform: scale(1.05);
    opacity: 1;
  }
`;

// Glossy highlight movement and color shift
const highlightMove = keyframes`
  0% {
    top: 10%;
    left: 15%;
    background: radial-gradient(
      circle at 30% 30%,
      rgba(255, 255, 255, 0.95) 0%,
      rgba(255, 255, 255, 0.5) 40%,
      transparent 70%
    );
  }
  25% {
    top: 12%;
    left: 18%;
    background: radial-gradient(
      circle at 30% 30%,
      rgba(255, 250, 255, 0.95) 0%,
      rgba(250, 245, 255, 0.5) 40%,
      transparent 70%
    );
  }
  50% {
    top: 15%;
    left: 20%;
    background: radial-gradient(
      circle at 30% 30%,
      rgba(248, 245, 255, 0.95) 0%,
      rgba(240, 235, 255, 0.5) 40%,
      transparent 70%
    );
  }
  75% {
    top: 12%;
    left: 18%;
    background: radial-gradient(
      circle at 30% 30%,
      rgba(255, 252, 255, 0.95) 0%,
      rgba(250, 240, 255, 0.5) 40%,
      transparent 70%
    );
  }
  100% {
    top: 10%;
    left: 15%;
    background: radial-gradient(
      circle at 30% 30%,
      rgba(255, 255, 255, 0.95) 0%,
      rgba(255, 255, 255, 0.5) 40%,
      transparent 70%
    );
  }
`;

// Subtle expanding ripple for voice activity - slow and smooth
const rippleExpand = keyframes`
  0% {
    transform: scale(0.9);
    opacity: 0;
  }
  20% {
    opacity: 0.5;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
`;

// Medium speed wave
const rippleExpandMedium = keyframes`
  0% {
    transform: scale(0.85);
    opacity: 0;
  }
  20% {
    opacity: 0.4;
  }
  100% {
    transform: scale(1.35);
    opacity: 0;
  }
`;

// Fast wave for variety
const rippleExpandFast = keyframes`
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  20% {
    opacity: 0.6;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
`;

// Container for the demo
const DemoContainer = styled.div`
  position: relative;
  width: 250px;
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  margin: 0 auto;
`;

// Voice agent core sphere - using theme.primary #796CFF
const VoiceAgentCore = styled.div`
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    #f0eeff 0%,
    #e6e0ff 15%,
    #d8d0ff 30%,
    #c8bdff 45%,
    #bdb3ff 60%,
    #d0c8ff 75%,
    #ebe6ff 90%,
    #ffffff 100%
  );
  background-size: 300% 300%;
  animation:
    ${iridescentShift} 8s ease-in-out infinite,
    ${voicePulse} 2s ease-in-out infinite;
  box-shadow:
    0 8px 25px rgba(121, 108, 255, 0.15),
    inset -8px -8px 20px rgba(121, 108, 255, 0.05),
    inset 8px 8px 20px rgba(255, 255, 255, 0.9),
    0 0 40px rgba(121, 108, 255, 0.3);
  z-index: 10;

  /* Main glossy highlight - moving and color shifting */
  &::before {
    content: '';
    position: absolute;
    top: 10%;
    left: 15%;
    width: 45%;
    height: 45%;
    border-radius: 50%;
    background: radial-gradient(
      circle at 30% 30%,
      rgba(255, 255, 255, 0.95) 0%,
      rgba(255, 255, 255, 0.5) 40%,
      transparent 70%
    );
    animation: ${highlightMove} 6s ease-in-out infinite;
  }

  /* Inner glow pulse for voice activity - theme.primary */
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 80%;
    height: 80%;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: radial-gradient(
      circle at 50% 50%,
      rgba(121, 108, 255, 0.35) 0%,
      rgba(121, 108, 255, 0.2) 30%,
      transparent 70%
    );
    animation: ${voicePulse} 2s ease-in-out infinite;
  }
`;

// Subtle ripple ring for voice activity indicator - theme.primary
type WaveSpeed = 'slow' | 'medium' | 'fast';

const VoiceRipple = styled.div<{
  thickness?: string;
  opacity?: number;
  speed?: WaveSpeed;
  duration?: number;
  delay?: number;
}>`
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100px;
  height: 100px;
  margin: -50px 0 0 -50px;
  border-radius: 50%;
  border: ${({ thickness }) => thickness || '1.5px'} solid
    rgba(121, 108, 255, ${({ opacity }) => opacity || 0.4});
  animation: ${({ speed }) =>
      speed === 'slow'
        ? rippleExpand
        : speed === 'medium'
          ? rippleExpandMedium
          : rippleExpandFast}
    ${({ duration }) => duration || 3}s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  animation-delay: ${({ delay }) => delay || 0}s;
  z-index: 5;
`;

// Rain droplet effect - falling from top
const rainFall = keyframes`
  0% {
    top: -20px;
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.4;
  }
  100% {
    top: 270px;
    opacity: 0;
  }
`;

// Rain droplet styled component
const RainDrop = styled.div<{
  left?: string;
  size?: string;
  height?: string;
  opacity?: number;
  duration?: number;
  delay?: number;
}>`
  position: absolute;
  top: -20px;
  left: ${({ left }) => left || '50%'};
  width: ${({ size }) => size || '2px'};
  height: ${({ height }) => height || '8px'};
  background: linear-gradient(
    to bottom,
    rgba(121, 108, 255, 0) 0%,
    rgba(121, 108, 255, ${({ opacity }) => opacity || 0.5}) 50%,
    rgba(121, 108, 255, 0) 100%
  );
  border-radius: 50%;
  animation: ${rainFall} ${({ duration }) => duration || 2}s linear infinite;
  animation-delay: ${({ delay }) => delay || 0}s;
  z-index: 1;
`;

// Orbiting particles animation - smaller orbit radius
const orbit = keyframes`
  0% {
    transform: rotate(0deg) translateX(65px) rotate(0deg);
    opacity: 0.2;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    transform: rotate(360deg) translateX(65px) rotate(-360deg);
    opacity: 0.2;
  }
`;

// Orbiting particle component
const OrbitingParticle = styled.div<{
  size?: string;
  duration?: number;
  delay?: number;
}>`
  position: absolute;
  top: 50%;
  left: 50%;
  width: ${({ size }) => size || '3px'};
  height: ${({ size }) => size || '3px'};
  background: radial-gradient(
    circle,
    rgba(121, 108, 255, 0.9) 0%,
    rgba(121, 108, 255, 0.4) 50%,
    transparent 100%
  );
  border-radius: 50%;
  animation: ${orbit} ${({ duration }) => duration || 8}s ease-in-out infinite;
  animation-delay: ${({ delay }) => delay || 0}s;
  z-index: 3;
  box-shadow: 0 0 6px rgba(121, 108, 255, 0.5);
`;

// Sparkle/twinkle animation - smoother
const sparkle = keyframes`
  0%, 100% {
    opacity: 0;
    transform: scale(0.5);
  }
  50% {
    opacity: 0.9;
    transform: scale(1);
  }
`;

// Sparkle component - smaller and smoother
const Sparkle = styled.div<{
  top?: string;
  left?: string;
  size?: string;
  duration?: number;
  delay?: number;
}>`
  position: absolute;
  top: ${({ top }) => top || '50%'};
  left: ${({ left }) => left || '50%'};
  width: ${({ size }) => size || '2.5px'};
  height: ${({ size }) => size || '2.5px'};
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  animation: ${sparkle} ${({ duration }) => duration || 2}s
    cubic-bezier(0.4, 0, 0.6, 1) infinite;
  animation-delay: ${({ delay }) => delay || 0}s;
  z-index: 8;
  box-shadow: 0 0 5px rgba(121, 108, 255, 0.7);

  &::before,
  &::after {
    content: '';
    position: absolute;
    background: rgba(255, 255, 255, 0.7);
  }

  &::before {
    top: 50%;
    left: -3px;
    width: 10px;
    height: 0.8px;
    transform: translateY(-50%);
  }

  &::after {
    left: 50%;
    top: -3px;
    width: 0.8px;
    height: 10px;
    transform: translateX(-50%);
  }
`;

// Energy arc rotation
const arcFlow = keyframes`
  0% {
    transform: rotate(0deg);
    opacity: 0.4;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    transform: rotate(360deg);
    opacity: 0.4;
  }
`;

// Energy arc component
const EnergyArc = styled.div<{
  duration?: number;
  delay?: number;
}>`
  position: absolute;
  top: 50%;
  left: 50%;
  width: 140px;
  height: 140px;
  margin: -70px 0 0 -70px;
  border-radius: 50%;
  border: 1.5px solid transparent;
  border-top-color: rgba(121, 108, 255, 0.5);
  border-right-color: rgba(121, 108, 255, 0.25);
  animation: ${arcFlow} ${({ duration }) => duration || 6}s ease-in-out infinite;
  animation-delay: ${({ delay }) => delay || 0}s;
  z-index: 4;
  filter: blur(1.5px);
`;

/**
 * GradientOrbDemo Component
 *
 * Voice Agent Animation - A beautiful iridescent sphere with circular frequency
 * visualization representing voice/audio activity.
 *
 * Features:
 * - Glossy iridescent core sphere with breathing animation
 * - Circular frequency bars pulsing around the sphere (like audio waveform)
 * - Expanding wave rings emanating from center (voice activity indicator)
 * - Smooth color transitions and glowing effects
 * - Compact 250px canvas suitable for voice agent UI
 *
 * Perfect for:
 * - Voice assistant interfaces
 * - AI agent listening/speaking states
 * - Audio/voice activity visualization
 *
 * @example
 * ```jsx
 * import GradientOrbDemo from '@unpod/components/common/GradientOrb/demo';
 *
 * function VoiceAgentUI() {
 *   return (
 *     <div>
 *       <GradientOrbDemo />
 *       <input placeholder="Ask me anything..." />
 *     </div>
 *   );
 * }
 * ```
 */
const GradientOrbDemo = () => {
  // Balanced wave rings - 5 waves with smooth, evenly distributed timing
  const waves: Array<{
    duration: number;
    delay: number;
    opacity: number;
    thickness: string;
    speed: WaveSpeed;
  }> = [
    {
      duration: 4.5,
      delay: 0,
      opacity: 0.4,
      thickness: '1.5px',
      speed: 'medium',
    },
    {
      duration: 4.5,
      delay: 0.9,
      opacity: 0.35,
      thickness: '1.3px',
      speed: 'medium',
    },
    {
      duration: 4.5,
      delay: 1.8,
      opacity: 0.3,
      thickness: '1.1px',
      speed: 'medium',
    },
    {
      duration: 4.5,
      delay: 2.7,
      opacity: 0.25,
      thickness: '1px',
      speed: 'medium',
    },
    {
      duration: 4.5,
      delay: 3.6,
      opacity: 0.2,
      thickness: '0.8px',
      speed: 'medium',
    },
  ];

  // Subtle rain effect - 6 droplets evenly spaced
  const rainDrops = [
    {
      left: '20%',
      duration: 2.5,
      delay: 0,
      height: '10px',
      size: '1.5px',
      opacity: 0.35,
    },
    {
      left: '35%',
      duration: 2.5,
      delay: 0.4,
      height: '9px',
      size: '1.3px',
      opacity: 0.3,
    },
    {
      left: '50%',
      duration: 2.5,
      delay: 0.8,
      height: '11px',
      size: '1.6px',
      opacity: 0.32,
    },
    {
      left: '65%',
      duration: 2.5,
      delay: 1.2,
      height: '10px',
      size: '1.4px',
      opacity: 0.28,
    },
    {
      left: '80%',
      duration: 2.5,
      delay: 1.6,
      height: '9px',
      size: '1.3px',
      opacity: 0.3,
    },
    {
      left: '42%',
      duration: 2.5,
      delay: 2.0,
      height: '10px',
      size: '1.5px',
      opacity: 0.33,
    },
  ];

  // Orbiting particles - 4 particles evenly distributed
  const particles = [
    { duration: 12, delay: 0, size: '3px' },
    { duration: 12, delay: 3, size: '3px' },
    { duration: 12, delay: 6, size: '3px' },
    { duration: 12, delay: 9, size: '3px' },
  ];

  // Sparkles - 4 sparkles at cardinal positions
  const sparkles = [
    { top: '20%', left: '50%', duration: 3.5, delay: 0, size: '2.5px' },
    { top: '50%', left: '80%', duration: 3.5, delay: 0.875, size: '2.5px' },
    { top: '80%', left: '50%', duration: 3.5, delay: 1.75, size: '2.5px' },
    { top: '50%', left: '20%', duration: 3.5, delay: 2.625, size: '2.5px' },
  ];

  // Energy arcs - 2 arcs for smooth flow
  const energyArcs = [
    { duration: 12, delay: 0 },
    { duration: 12, delay: 6 },
  ];

  return (
    <DemoContainer>
      {/* Rain effect - subtle droplets falling */}
      {rainDrops.map((drop, i) => (
        <RainDrop
          key={`rain-${i}`}
          left={drop.left}
          duration={drop.duration}
          delay={drop.delay}
          height={drop.height}
          size={drop.size}
          opacity={drop.opacity}
        />
      ))}

      {/* Orbiting particles around the sphere */}
      {particles.map((particle, i) => (
        <OrbitingParticle
          key={`particle-${i}`}
          duration={particle.duration}
          delay={particle.delay}
          size={particle.size}
        />
      ))}

      {/* Sparkles at cardinal points */}
      {sparkles.map((sparkle, i) => (
        <Sparkle
          key={`sparkle-${i}`}
          top={sparkle.top}
          left={sparkle.left}
          duration={sparkle.duration}
          delay={sparkle.delay}
          size={sparkle.size}
        />
      ))}

      {/* Energy arcs flowing around */}
      {energyArcs.map((arc, i) => (
        <EnergyArc key={`arc-${i}`} duration={arc.duration} delay={arc.delay} />
      ))}

      {/* Balanced wave rings */}
      {waves.map((wave, i) => (
        <VoiceRipple
          key={`wave-${i}`}
          speed={wave.speed}
          duration={wave.duration}
          delay={wave.delay}
          opacity={wave.opacity}
          thickness={wave.thickness}
        />
      ))}

      {/* Voice agent core sphere */}
      <VoiceAgentCore />
    </DemoContainer>
  );
};

export default GradientOrbDemo;
