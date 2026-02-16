import styled, { keyframes } from 'styled-components';

const pulse = keyframes`
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
`;

/* ── Page root ── */
export const StyledRoot = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #eef1f5;
  overflow: hidden;
`;

/* ── Dot‑grid overlay ── */
export const StyledDotPattern = styled.div`
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #bcc5d0 1.2px, transparent 1.2px);
  background-size: 20px 20px;
  opacity: 0.5;
  pointer-events: none;
  z-index: 0;
`;

/* ── Centre radial glow ── */
export const StyledRadialGlow = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 85%;
  height: 85%;
  background: radial-gradient(
    ellipse at center,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.7) 35%,
    rgba(255, 255, 255, 0) 65%
  );
  pointer-events: none;
  z-index: 1;
`;

/* ── Top‑left blue diamonds ── */
export const StyledTopLeftDiamonds = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 220px;
  height: 200px;
  pointer-events: none;
  z-index: 2;
  overflow: hidden;

  /* Back diamond – lighter blue */
  &::before {
    content: '';
    position: absolute;
    top: -70px;
    left: -70px;
    width: 190px;
    height: 190px;
    background: #60a5fa;
    transform: rotate(45deg);
  }

  /* Front diamond – darker blue, overlapping */
  &::after {
    content: '';
    position: absolute;
    top: -90px;
    left: 30px;
    width: 190px;
    height: 190px;
    background: #2563eb;
    transform: rotate(45deg);
  }

  @media (max-width: 768px) {
    width: 140px;
    height: 130px;

    &::before {
      width: 130px;
      height: 130px;
    }

    &::after {
      width: 130px;
      height: 130px;
      left: 15px;
    }
  }
`;

/* ── Bottom‑right 3‑D stair blocks ── */
export const StyledBottomRightBlocks = styled.div`
  position: absolute;
  bottom: 0;
  right: 0;
  width: 280px;
  height: 240px;
  pointer-events: none;
  z-index: 2;
  overflow: hidden;

  @media (max-width: 768px) {
    width: 180px;
    height: 160px;
  }
`;

export const StyledBlock = styled.div<{
  $w: number;
  $h: number;
  $bottom: number;
  $right: number;
  $bg: string;
  $skewX?: number;
}>`
  position: absolute;
  bottom: ${({ $bottom }) => $bottom}px;
  right: ${({ $right }) => $right}px;
  width: ${({ $w }) => $w}px;
  height: ${({ $h }) => $h}px;
  background: ${({ $bg }) => $bg};
  transform: skewX(${({ $skewX }) => $skewX ?? 0}deg);

  @media (max-width: 768px) {
    width: ${({ $w }) => $w * 0.65}px;
    height: ${({ $h }) => $h * 0.65}px;
    bottom: ${({ $bottom }) => $bottom * 0.65}px;
    right: ${({ $right }) => $right * 0.65}px;
  }
`;

/* ── Filled chevron arrows (left side >>>>) ── */
export const StyledChevronsLeft = styled.div`
  position: absolute;
  left: 40px;
  top: 38%;
  display: flex;
  gap: 3px;
  z-index: 2;
  pointer-events: none;

  @media (max-width: 1024px) {
    display: none;
  }
`;

export const StyledChevron = styled.span<{ $direction?: 'left' | 'right' }>`
  display: inline-block;
  width: 0;
  height: 0;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  ${({ $direction }) =>
    $direction === 'left'
      ? 'border-right: 12px solid #b0b8c4;'
      : 'border-left: 12px solid #b0b8c4;'}
`;

/* ── Filled chevron arrows (right side <<<<) ── */
export const StyledChevronsRight = styled.div`
  position: absolute;
  right: 40px;
  top: 35%;
  display: flex;
  gap: 3px;
  z-index: 2;
  pointer-events: none;

  @media (max-width: 1024px) {
    display: none;
  }
`;

/* ── Scope / target circles ── */
export const StyledScopeCircle = styled.div<{
  $top?: string;
  $left?: string;
  $right?: string;
  $bottom?: string;
  $size?: number;
}>`
  position: absolute;
  top: ${({ $top }) => $top || 'auto'};
  left: ${({ $left }) => $left || 'auto'};
  right: ${({ $right }) => $right || 'auto'};
  bottom: ${({ $bottom }) => $bottom || 'auto'};
  width: ${({ $size }) => $size || 60}px;
  height: ${({ $size }) => $size || 60}px;
  border-radius: 50%;
  border: 2.5px solid #c3ced9;
  opacity: 0.55;
  pointer-events: none;
  z-index: 2;

  /* Vertical cross line */
  &::before {
    content: '';
    position: absolute;
    top: 25%;
    left: 50%;
    width: 2px;
    height: 50%;
    background: #c3ced9;
    transform: translateX(-50%);
  }

  /* Horizontal cross line */
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 25%;
    width: 50%;
    height: 2px;
    background: #c3ced9;
    transform: translateY(-50%);
  }

  @media (max-width: 768px) {
    display: none;
  }
`;

/* ── Unpod logo (top‑right) ── */
export const StyledLogo = styled.div`
  position: absolute;
  top: 30px;
  right: 40px;
  z-index: 3;

  img {
    height: 72px;
    width: auto;
  }

  @media (max-width: 768px) {
    top: 16px;
    right: 16px;

    img {
      height: 44px;
    }
  }
`;

/* ── Main content area (full‑page centred, like image) ── */
export const StyledContentArea = styled.div`
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 40px 70px;
`;

/* ── Avatar – absolutely positioned on the left ── */
export const StyledAvatarSection = styled.div`
  position: absolute;
  left: 40px;
  bottom: 70px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  z-index: 4;

  @media (max-width: 1024px) {
    left: 20px;
    bottom: 60px;
  }

  @media (max-width: 768px) {
    position: relative;
    left: auto;
    bottom: auto;
  }
`;

export const StyledVideoAvatar = styled.video`
  width: 220px;
  height: 220px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #796cff;
  box-shadow: 0 8px 32px rgba(121, 108, 255, 0.25);
  background-color: #fff;
  animation: ${pulse} 3s ease-in-out infinite;

  @media (max-width: 768px) {
    width: 160px;
    height: 160px;
  }
`;

export const StyledVoiceSection = styled.div`
  display: flex;
  justify-content: center;
`;

/* ── Text section (centred on full page, matching image) ── */
export const StyledTextSection = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
`;

export const StyledHeadingPrimary = styled.h1`
  font-family: var(--font-montserrat), 'Montserrat', sans-serif;
  font-size: 80px;
  font-weight: 900;
  text-transform: uppercase;
  color: #312e81;
  line-height: 1.5;
  margin: 0 0 -4px;
  letter-spacing: -1px;
  text-shadow: 2px 2px 0 rgba(30, 27, 75, 0.15);

  @media (max-width: 1200px) {
    font-size: 62px;
  }

  @media (max-width: 768px) {
    font-size: 42px;
  }

  @media (max-width: 480px) {
    font-size: 32px;
  }
`;

export const StyledHeadingSecondary = styled.h2`
  font-family: var(--font-montserrat), 'Montserrat', sans-serif;
  font-size: 72px;
  font-weight: 900;
  font-style: normal;
  text-transform: uppercase;
  color: #111827;
  line-height: 1.2;
  margin: 0;
  letter-spacing: -0.5px;

  @media (max-width: 1200px) {
    font-size: 56px;
  }

  @media (max-width: 768px) {
    font-size: 36px;
  }

  @media (max-width: 480px) {
    font-size: 28px;
  }
`;

/* ── Badges row (single bordered strip with dividers) ── */
export const StyledBadgesRow = styled.div`
  display: inline-flex;
  margin-top: 28px;
  border: 1.5px solid #c5cdd8;
  border-radius: 4px;
  overflow: hidden;

  @media (max-width: 480px) {
    flex-direction: column;
  }
`;

export const StyledBadge = styled.div`
  font-family: var(--font-montserrat), 'Montserrat', sans-serif;
  padding: 10px 28px;
  font-size: 14px;
  font-weight: 800;
  text-transform: uppercase;
  color: #1a1e2e;
  letter-spacing: 1.2px;
  white-space: nowrap;

  & + & {
    border-left: 1.5px solid #c5cdd8;
  }

  @media (max-width: 768px) {
    padding: 8px 18px;
    font-size: 12px;
  }

  @media (max-width: 480px) {
    & + & {
      border-left: none;
      border-top: 1.5px solid #c5cdd8;
    }
  }
`;

/* ── Footer contact bar ── */
export const StyledFooterBar = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 36px;
  padding: 16px 48px;
  background: #eceef2;
  font-family: var(--font-montserrat), 'Montserrat', sans-serif;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  color: #1a1e2e;
  letter-spacing: 0.8px;

  a {
    color: #1a1e2e;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 8px;

    &:hover {
      color: #4338ca;
    }
  }

  @media (max-width: 768px) {
    flex-wrap: wrap;
    gap: 16px;
    padding: 12px 20px;
    font-size: 11px;
  }
`;
