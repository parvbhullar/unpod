'use client';
import styled from 'styled-components';
import { Card, Tag, Typography } from 'antd';

const { Title } = Typography;

const StyledTitle = styled(Title)`
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

const StyledSubTitle = styled.p`
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

const StyledDescription = styled.p`
  font-size: 18px !important;
  font-weight: 400 !important;
  max-width: 768px !important;
  margin-top: 40px !important;
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

const StyledCard = styled(Card)`
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
    text-align: center;

    @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      text-align: center;
    }
  }

  .ant-card-meta-description {
    font-size: 14px;
    text-align: center;

    @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
      text-align: center;
    }
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    align-items: center;
    text-align: center;
  }
`;

const StyledCardIcon = styled.div`
  background: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  font-size: 22px;
  font-weight: 600;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;
  margin-inline: auto;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    margin-left: auto;
    margin-right: auto;
  }
`;

const StyledGrid = styled.div`
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-top: 40px;

  @media screen and (min-width: ${({ theme }) => theme.breakpoints.lg}px) {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }
`;

const StyledIconWrapper = styled.div`
  display: flex;
  justify-content: center;
  color: ${({ theme }) => theme.palette.primary};
  align-items: center;
  gap: 8px;
  width: 100%;
  text-align: center;
`;
const Styledtext = styled.span`
  color: ${({ theme }) => theme.palette.text.heading};
`;

const StyledAiTag = styled(Tag)`
  background: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  font-size: 14px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 16px;
  display: inline-block;
  margin-bottom: 16px;
`;

export {
  StyledTitle,
  StyledSubTitle,
  StyledDescription,
  StyledCard,
  StyledCardIcon,
  StyledGrid,
  StyledIconWrapper,
  Styledtext,
  StyledAiTag,
};
