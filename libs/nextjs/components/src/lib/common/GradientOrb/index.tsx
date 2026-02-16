'use client';

import React, { CSSProperties } from 'react';
import styled, { keyframes } from 'styled-components';

const float = keyframes`
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(10px, -10px) scale(1.05);
  }
  66% {
    transform: translate(-10px, 10px) scale(0.95);
  }
`;

const rotate = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

type StyledGradientOrbProps = {
  position?: 'relative' | 'absolute' | 'fixed' | 'static';
  size?: string;
  variant?: 'purple' | 'blue' | 'cyan' | 'pink';
  blur?: string;
  opacity?: number;
  animate?: boolean;
  duration?: string;
  rotationDuration?: string;
  top?: string;
  bottom?: string;
  left?: string;
  right?: string;
  zIndex?: number;};

const StyledGradientOrb = styled.div<StyledGradientOrbProps>`
  position: ${({ position }) => position || 'relative'};
  width: ${({ size }) => size || '300px'};
  height: ${({ size }) => size || '300px'};
  border-radius: 50%;
  background: ${({ variant }) => {
    switch (variant) {
      case 'purple':
        return 'radial-gradient(circle at 30% 40%, rgba(200, 150, 255, 0.8), rgba(150, 100, 255, 0.6), rgba(100, 150, 255, 0.4))';
      case 'blue':
        return 'radial-gradient(circle at 30% 40%, rgba(150, 200, 255, 0.8), rgba(100, 150, 255, 0.6), rgba(150, 100, 255, 0.4))';
      case 'cyan':
        return 'radial-gradient(circle at 30% 40%, rgba(150, 255, 255, 0.8), rgba(100, 200, 255, 0.6), rgba(150, 150, 255, 0.4))';
      case 'pink':
        return 'radial-gradient(circle at 30% 40%, rgba(255, 150, 255, 0.8), rgba(255, 100, 200, 0.6), rgba(200, 100, 255, 0.4))';
      default:
        return 'radial-gradient(circle at 30% 40%, rgba(200, 150, 255, 0.8), rgba(150, 100, 255, 0.6), rgba(100, 150, 255, 0.4))';
    }
  }};
  filter: blur(${({ blur }) => blur || '40px'});
  opacity: ${({ opacity }) => opacity || 0.6};
  animation: ${({ animate }) => (animate ? float : 'none')}
    ${({ duration }) => duration || '10s'} ease-in-out infinite;
  ${({ top }) => top && `top: ${top};`}
  ${({ bottom }) => bottom && `bottom: ${bottom};`}
  ${({ left }) => left && `left: ${left};`}
  ${({ right }) => right && `right: ${right};`}
  ${({ zIndex }) => zIndex && `z-index: ${zIndex};`}
  pointer-events: none;
  user-select: none;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    background: radial-gradient(
      circle at 60% 50%,
      rgba(255, 255, 255, 0.4),
      rgba(255, 255, 255, 0) 50%
    );
    animation: ${({ animate }) => (animate ? rotate : 'none')}
      ${({ rotationDuration }) => rotationDuration || '20s'} linear infinite;
  }
`;

type GradientOrbProps = StyledGradientOrbProps & {
  className?: string;
  style?: CSSProperties;};

const GradientOrb: React.FC<GradientOrbProps> = ({
  size = '300px',
  variant = 'purple',
  blur = '40px',
  opacity = 0.6,
  animate = true,
  duration = '10s',
  rotationDuration = '20s',
  position = 'relative',
  top,
  bottom,
  left,
  right,
  zIndex,
  className,
  style,
}) => {
  return (
    <StyledGradientOrb
      size={size}
      variant={variant}
      blur={blur}
      opacity={opacity}
      animate={animate}
      duration={duration}
      rotationDuration={rotationDuration}
      position={position}
      top={top}
      bottom={bottom}
      left={left}
      right={right}
      zIndex={zIndex}
      className={className}
      style={style}
    />
  );
};

export default GradientOrb;
