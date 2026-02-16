import styled, { keyframes } from 'styled-components';

type SizeProps = {
  size?: number;};

type OrbitProps = {
  duration?: number;
  $reverse?: boolean;};

type DotProps = {
  dotSize?: number;
  gradient?: string;};

// Keyframe animations
const orbit = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const glowPulse = keyframes`
  0%, 100% {
    opacity: 0.5;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.2);
  }
`;

const antennaPulse = keyframes`
  0%, 100% {
    filter: drop-shadow(0 0 3px rgba(80, 70, 229, 0.6));
  }
  50% {
    filter: drop-shadow(0 0 12px rgba(80, 70, 229, 1));
  }
`;

const eyeLook = keyframes`
  /* Center - Looking forward (calm start) */
  0% {
    transform: translate(0, 0);
  }
  8% {
    transform: translate(0, 0);
  }

  /* Quick glance up */
  10% {
    transform: translate(0, -4px);
  }
  20% {
    transform: translate(0, -4px);
  }

  /* Return to center */
  22% {
    transform: translate(0, 0);
  }
  30% {
    transform: translate(0, 0);
  }

  /* Look right (longer hold - examining) */
  33% {
    transform: translate(4.5px, 0);
  }
  48% {
    transform: translate(4.5px, 0);
  }

  /* Back to center */
  51% {
    transform: translate(0, 0);
  }
  56% {
    transform: translate(0, 0);
  }

  /* Look up-right diagonal (natural scanning) */
  59% {
    transform: translate(3.5px, -3.5px);
  }
  68% {
    transform: translate(3.5px, -3.5px);
  }

  /* Center again */
  71% {
    transform: translate(0, 0);
  }
  77% {
    transform: translate(0, 0);
  }

  /* Quick look right */
  79% {
    transform: translate(4.5px, 0);
  }
  85% {
    transform: translate(4.5px, 0);
  }

  /* Brief look up */
  87% {
    transform: translate(0, -3.5px);
  }
  91% {
    transform: translate(0, -3.5px);
  }

  /* Rest at center */
  93% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(0, 0);
  }
`;

const eyeBlink = keyframes`
  /* Open - start */
  0%, 8.5% {
    transform: scaleY(0);
    opacity: 0;
  }
  /* Quick close */
  9% {
    transform: scaleY(1);
    opacity: 1;
  }
  /* Quick open */
  9.5%, 21.5% {
    transform: scaleY(0);
    opacity: 0;
  }
  /* Blink 2 */
  22% {
    transform: scaleY(1);
    opacity: 1;
  }
  22.5%, 50.5% {
    transform: scaleY(0);
    opacity: 0;
  }
  /* Blink 3 */
  51% {
    transform: scaleY(1);
    opacity: 1;
  }
  51.5%, 70.5% {
    transform: scaleY(0);
    opacity: 0;
  }
  /* Blink 4 */
  71% {
    transform: scaleY(1);
    opacity: 1;
  }
  71.5%, 85.5% {
    transform: scaleY(0);
    opacity: 0;
  }
  /* Blink 5 */
  86% {
    transform: scaleY(1);
    opacity: 1;
  }
  86.5%, 92.5% {
    transform: scaleY(0);
    opacity: 0;
  }
  /* Blink 6 */
  93% {
    transform: scaleY(1);
    opacity: 1;
  }
  93.5%, 100% {
    transform: scaleY(0);
    opacity: 0;
  }
`;

const pupilDilate = keyframes`
  /* Relaxed state */
  0%, 8% {
    transform: scale(1);
  }

  /* Slightly focused (looking up) */
  10%, 20% {
    transform: scale(0.85);
  }

  /* Relaxed at center */
  22%, 30% {
    transform: scale(1);
  }

  /* Very focused (examining right - interested) */
  33%, 48% {
    transform: scale(1.3);
  }

  /* Return to normal */
  51%, 56% {
    transform: scale(1);
  }

  /* Curious (up-right diagonal) */
  59%, 68% {
    transform: scale(1.15);
  }

  /* Relaxed */
  71%, 77% {
    transform: scale(1);
  }

  /* Alert (quick look right) */
  79%, 85% {
    transform: scale(0.9);
  }

  /* Attentive (brief up) */
  87%, 91% {
    transform: scale(0.95);
  }

  /* Back to relaxed */
  93%, 100% {
    transform: scale(1);
  }
`;

const corneaShimmer = keyframes`
  0%, 100% {
    opacity: 0.9;
  }
  50% {
    opacity: 0.6;
  }
`;

const eyeShine = keyframes`
  0%, 100% {
    opacity: 0.7;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
    transform: scale(0.85);
  }
`;

const scleraShadow = keyframes`
  0%, 100% {
    opacity: 0.08;
  }
  50% {
    opacity: 0.12;
  }
`;

// Ear animations
const earWiggle = keyframes`
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-5deg);
  }
  50% {
    transform: rotate(3deg);
  }
  75% {
    transform: rotate(-2deg);
  }
`;

const earPulse = keyframes`
  0%, 100% {
    filter: brightness(1) drop-shadow(0 0 0px #5046e5);
    opacity: 1;
  }
  50% {
    filter: brightness(1.15) drop-shadow(0 0 8px #5046e5);
    opacity: 0.92;
  }
`;

const soundWave = keyframes`
  0% {
    r: 0;
    opacity: 0.7;
    stroke-width: 2;
  }
  100% {
    r: 50;
    opacity: 0;
    stroke-width: 0.5;
  }
`;

const ledBlink = keyframes`
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 0.2;
  }
`;

// Styled components
export const StyledOrbitContainer = styled.div<SizeProps>`
  position: relative;
  width: ${(props) => props.size || 320}px;
  height: ${(props) => props.size || 320}px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const StyledOrbitLogo = styled.div<SizeProps>`
  position: relative;
  width: ${(props) => (props.size ? props.size * 0.5625 : 180)}px;
  height: ${(props) => (props.size ? props.size * 0.625 : 200)}px;
  z-index: 2;
`;

export const StyledOrbitWrapper = styled.div<SizeProps>`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: ${(props) => (props.size ? props.size * 0.8125 : 260)}px;
  height: ${(props) => (props.size ? props.size * 0.8125 : 260)}px;
`;

export const StyledOrbit = styled.div<OrbitProps>`
  position: absolute;
  width: 100%;
  height: 100%;
  animation: ${orbit} ${(props) => props.duration || 3}s linear infinite;
  animation-direction: ${(props) => (props.$reverse ? 'reverse' : 'normal')};
`;

export const StyledOrbitDot = styled.div<DotProps>`
  position: absolute;
  width: ${(props) => props.dotSize || 12}px;
  height: ${(props) => props.dotSize || 12}px;
  background: ${(props) =>
    props.gradient || 'linear-gradient(135deg, #5046e5, #818cf8)'};
  border-radius: 50%;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  box-shadow: 0 0 15px rgba(80, 70, 229, 0.8);
`;

export const StyledGlow = styled.div<SizeProps>`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: ${(props) => (props.size ? props.size * 0.625 : 200)}px;
  height: ${(props) => (props.size ? props.size * 0.625 : 200)}px;
  background: radial-gradient(
    circle,
    rgba(80, 70, 229, 0.3) 0%,
    transparent 70%
  );
  animation: ${glowPulse} 2s ease-in-out infinite;
  z-index: 1;
`;

export const StyledUnpodLogo = styled.svg`
  width: 100%;
  height: 100%;
  overflow: visible;

  .body {
    fill: #5046e5;
  }

  .visor {
    fill: #e5e7eb;
  }

  .eye {
    fill: #5046e5;
  }

  .antenna-ball {
    fill: #5046e5;
    animation: ${antennaPulse} 1.5s ease-in-out infinite;
  }

  .sclera {
    fill: #f8f9fa;
  }

  .sclera-shadow {
    fill: #000000;
    opacity: 0.08;
    animation: ${scleraShadow} 4s ease-in-out infinite;
  }

  .pupil-group {
    animation: ${eyeLook} 8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  }

  .iris {
    fill: url(#irisGradient);
  }

  .pupil {
    fill: #000000;
    transform-origin: center;
    animation: ${pupilDilate} 8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  }

  .cornea {
    fill: #ffffff;
    opacity: 0.9;
    animation: ${corneaShimmer} 3s ease-in-out infinite;
  }

  .eye-shine {
    fill: #ffffff;
    opacity: 0.7;
    animation: ${eyeShine} 2.5s ease-in-out infinite;
  }

  .eyelid {
    fill: #5046e5;
    transform-origin: center;
    opacity: 0;
    animation: ${eyeBlink} 8s linear infinite;
  }

  .iris-glow {
    fill: #5046e5;
    opacity: 0.2;
    filter: blur(2px);
  }

  /* Ear styling and animations */
  .left-ear,
  .right-ear {
    transform-origin: center center;
    transition: all 0.3s ease-in-out;
  }

  .ear-outer {
    transition: all 0.3s ease;
  }

  .speaker-grill {
    transition: opacity 0.3s ease;
  }

  .sound-wave-1 {
    animation: ${soundWave} 1.5s ease-out infinite;
  }

  .sound-wave-2 {
    animation: ${soundWave} 1.5s ease-out infinite 0.2s;
  }

  .sound-wave-3 {
    animation: ${soundWave} 1.5s ease-out infinite 0.4s;
  }

  .ear-led {
    animation: ${ledBlink} 2s ease-in-out infinite;
  }

  .ear-highlight {
    transition: opacity 0.3s ease;
  }

  /* Subtle idle wiggle effect - occasional ear movement */
  .left-ear {
    animation: ${earWiggle} 12s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
  }

  .right-ear {
    animation: ${earWiggle} 12s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite
      0.6s;
  }

  /* Hover state - ears become more attentive */
  &:hover .left-ear,
  &:hover .right-ear {
    animation: ${earPulse} 1.8s ease-in-out infinite;
  }

  &:hover .sound-wave-1,
  &:hover .sound-wave-2,
  &:hover .sound-wave-3 {
    opacity: 0.5;
  }
`;
