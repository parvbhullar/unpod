'use client';
import styled from 'styled-components';
import { Steps } from 'antd';

export const CustomSteps = styled(Steps)`
  display: flex;
  flex-direction: row !important;
  align-items: center;

  .ant-steps-item-icon {
    flex-shrink: 0 !important;
  }

  .ant-steps-item-content {
    @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      display: flex;
      flex-direction: column;
    }
  }

  .ant-steps-item-container {
    display: flex;
    align-items: center;
  }

  .ant-steps-item-title {
    font-size: ${({ theme }) => theme.font.size.base} !important;
    font-weight: ${({ theme }) => theme.font.weight.semiBold} !important;
    margin-bottom: 0 !important;
    line-height: 13px !important;
    font-family: ${({ theme }) => theme.font.family} !important;
  }

  .ant-steps-item-description {
    display: flex;
    font-size: ${({ theme }) => theme.font.size.sm} !important;
    color: ${({ theme }) => theme.palette.text.secondary};
    font-family: ${({ theme }) => theme.font.family} !important;
    white-space: nowrap !important;
    padding: 0 !important;
  }

  .ant-steps-item-icon {
    font-size: ${({ theme }) => theme.font.size.base} !important;
    font-family: ${({ theme }) => theme.font.family} !important;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      margin-bottom: 13px !important;
    }
  }

  .ant-steps-item {
    font-size: ${({ theme }) => theme.font.size.sm} !important;
    font-family: ${({ theme }) => theme.font.family} !important;
  }
`;

export const StyledStepsIcon = styled.div`
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: ${({ theme }) => theme.palette.background.component};
  color: ${({ theme }) => theme.palette.text.secondary};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  border: 2px solid ${({ theme }) => theme.border.color};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};

  &.active {
    background: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.common.white};
    border: 1px solid ${({ theme }) => theme.palette.primary};
  }

  &.success {
    background: ${({ theme }) => theme.palette.success};
    color: ${({ theme }) => theme.palette.common.white};
    border: 1px solid ${({ theme }) => theme.palette.success};
  }
`;
