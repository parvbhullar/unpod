'use client';
import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

export const StyledContent = styled.div`
  display: inline-block;

  .step-title {
    font-size: ${({ theme }) => theme.font.size.base};
    font-weight: ${({ theme }) => theme.font.weight.semiBold};
  }

  .step-description {
    font-size: ${({ theme }) => theme.font.size.sm};
  }
`;

export const StyledStep = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: ${({ theme }) => theme.palette.background.component};
  border: 2px solid ${({ theme }) => theme.border.color};
  font-size: 16px;

  &.active {
    background-color: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.common.white};
    border-color: ${({ theme }) => theme.palette.primary};
  }

  &.success {
    background-color: ${({ theme }) => theme.palette.success};
    color: ${({ theme }) => theme.palette.common.white};
    border-color: ${({ theme }) => theme.palette.success};
  }
`;
