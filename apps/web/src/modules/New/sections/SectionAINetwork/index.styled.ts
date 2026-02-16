'use client';
import styled from 'styled-components';
import { Card, Typography } from 'antd';

const { Title } = Typography;

export const StyledTitle = styled(Title)`
  font-size: 48px !important;
  font-weight: 700 !important;
  margin-bottom: 16px !important;
  text-align: center;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 40px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 72px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 32px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 22px !important;
  }
`;

export const StyledSubTitle = styled.p`
  font-size: 18px !important;
  font-weight: 400 !important;
  max-width: 768px !important;
  margin-inline: auto !important;
  text-align: center;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 14px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    max-width: 340px !important;
  }
`;

export const StyledCard = styled(Card)`
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.palette.primary};
  background: ${({ theme }) => theme.palette.background.default};
  transition: all 300ms ease;

  &:hover {
    box-shadow: ${({ theme }) => theme.component.card.boxShadow};
    transform: scale(1.05);
  }

  .ant-card-meta-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 16px;
    color: ${({ theme }) => theme.palette.text.heading};

    @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      text-align: center;
    }
  }

  .ant-card-meta-description {
    font-size: 14px;

    @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      text-align: center;
    }
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    align-items: center;
    text-align: center;
  }
`;

export const StyledCardIcon = styled.div`
  background: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    margin-left: auto;
    margin-right: auto;
  }
`;

export const StyledGrid = styled.div`
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-top: 60px;

  @media screen and (min-width: ${({ theme }) => theme.breakpoints.lg}px) {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }
`;
