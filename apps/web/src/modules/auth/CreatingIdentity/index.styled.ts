'use client';
import styled, { keyframes } from 'styled-components';
import { Typography } from 'antd';

const pulse = keyframes`
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(22, 119, 255, 0.4);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 0 0 20px rgba(22, 119, 255, 0);
  }
`;

const rotate = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const shimmer = keyframes`
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
`;

const dotPulse = keyframes`
  0%, 80%, 100% {
    opacity: 0.3;
  }
  40% {
    opacity: 1;
  }
`;

const progressShine = keyframes`
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
`;

const progressPulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.85;
  }
`;

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 30px;
  width: 100%;
  max-width: 530px;
  margin: 0 auto;
  text-align: center;
`;

export const LogoWrapper = styled.div`
  position: relative;
  width: 140px;
  height: 140px;
  margin-bottom: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const LogoInner = styled.div`
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  animation: ${pulse} 2s ease-in-out infinite;
  z-index: 2;
`;

export const SpinnerRing = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid ${({ theme }) => theme.border.color};
  border-top-color: ${({ theme }) => theme.palette.primary};
  border-radius: 50%;
  animation: ${rotate} 1.2s linear infinite;
`;

export const OuterGlow = styled.div`
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border: 1px solid ${({ theme }) => theme.palette.primary}20;
  border-radius: 50%;
  animation: ${pulse} 2s ease-in-out infinite;
  animation-delay: 0.5s;
`;

export const StyledTitle = styled(Typography.Title)`
  margin-bottom: 12px !important;
  animation: ${fadeIn} 0.6s ease-out;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 24px !important;
  }
`;

export const StyledSubtitle = styled(Typography.Paragraph)`
  font-size: 16px;
  color: ${({ theme }) => theme.palette.text.secondary};
  margin-bottom: 32px !important;
  animation: ${fadeIn} 0.6s ease-out 0.1s both;
`;

export const StatusWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: 24px;
  animation: ${fadeIn} 0.6s ease-out 0.2s both;
`;

export const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${({ theme }) => theme.palette.success};
  animation: ${dotPulse} 1.5s ease-in-out infinite;
`;

export const StatusText = styled.span`
  font-size: 14px;
  color: ${({ theme }) => theme.palette.text.secondary};
  background: linear-gradient(
    90deg,
    ${({ theme }) => theme.palette.text.secondary} 0%,
    ${({ theme }) => theme.palette.text.primary} 50%,
    ${({ theme }) => theme.palette.text.secondary} 100%
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: ${shimmer} 3s linear infinite;
`;

export const SecureText = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 40px;
  font-size: 12px;
  color: ${({ theme }) => theme.palette.text.secondary};
  opacity: 0.7;
  animation: ${fadeIn} 0.6s ease-out 0.3s both;
`;

export const ProgressWrapper = styled.div`
  width: 100%;
  max-width: 400px;
  margin-top: 32px;
  animation: ${fadeIn} 0.6s ease-out 0.25s both;
`;

export const ProgressBarContainer = styled.div`
  width: 100%;
  height: 8px;
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: 4px;
  overflow: hidden;
  position: relative;
`;

export const ProgressBarFill = styled.div<{ $progress: number }>`
  height: 100%;
  background: linear-gradient(
    90deg,
    ${({ theme }) => theme.palette.primary} 0%,
    ${({ theme }) => theme.palette.primary}cc 100%
  );
  border-radius: 4px;
  width: ${({ $progress }) => $progress}%;
  transition: width 0.5s ease-out;
  position: relative;
  overflow: hidden;
  animation: ${progressPulse} 2s ease-in-out infinite;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.3) 50%,
      transparent 100%
    );
    animation: ${progressShine} 1.5s ease-in-out infinite;
  }
`;

export const ProgressInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
`;

export const ProgressStep = styled.span`
  font-size: 13px;
  color: ${({ theme }) => theme.palette.text.secondary};
`;

export const ProgressPercent = styled.span`
  font-size: 13px;
  font-weight: 500;
  color: ${({ theme }) => theme.palette.primary};
`;
