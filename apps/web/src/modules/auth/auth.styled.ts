'use client';
import styled, { css, keyframes } from 'styled-components';
import { Avatar, Typography } from 'antd';

export const StyledAuthContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30px;
  width: 600px;
  max-width: 100%;
  margin: 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
    padding: 0;
  }
`;

export const StyledHeader = styled.div`
  text-align: center;
  padding-bottom: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
`;

export const StyledAuthTitle = styled(Typography.Title)<{ $mb?: number }>`
  margin: 0 !important;
  margin-bottom: ${({ $mb }) => $mb ?? 0}px !important;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 30px !important;
  }
`;

export const StyledContentWrapper = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  margin-top: 14px;
`;

export const StyledAuthContent = styled(Typography.Paragraph)`
  font-size: 18px;
  margin-bottom: 8px !important;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 16px;
  }
`;

export const StyledAvatar = styled(Avatar)`
  background-color: ${({ theme }) => theme.palette.error};
  margin-bottom: 24px;
`;

const flipIn = keyframes`
  0% {
    transform: rotateY(90deg);
    opacity: 0;
  }
  100% {
    transform: rotateY(0deg);
    opacity: 1;
  }
`;

const flipOut = keyframes`
  0% {
    transform: rotateY(0deg);
    opacity: 1;
  }
  100% {
    transform: rotateY(-90deg);
    opacity: 0;
  }
`;

export const FlipCard = styled.div<{ $flipType?: 'in' | 'out' }>`
  width: 100%;
  backface-visibility: hidden;
  animation: ${({ $flipType }) =>
    $flipType === 'in'
      ? css`
          ${flipIn} 0.5s forwards
        `
      : $flipType === 'out'
        ? css`
            ${flipOut} 0.5s forwards
          `
        : 'none'};
`;

export const FlipContainer = styled.div`
  perspective: 1000px;
`;
