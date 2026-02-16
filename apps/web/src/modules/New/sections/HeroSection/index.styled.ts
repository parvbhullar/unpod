'use client';
import styled from 'styled-components';
import { Button, Typography } from 'antd';

const { Text, Title, Paragraph } = Typography;

const StyledPillTag = styled(Text)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(
    90deg,
    rgba(55, 125, 255, 0.15) 0%,
    rgba(168, 57, 255, 0.15) 100%
  );
  color: ${({ theme }) => theme.palette.text.heading};
  font-size: 0.9rem;
  border-radius: 999px;
  padding: 6px 12px;
  margin: 0 auto 32px;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    font-size: 18px !important;
  }
`;

const StyledHeading = styled(Title).attrs({ level: 1 })`
  font-size: 4rem !important;
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.text.heading};
  line-height: 1.15;
  text-align: center;
  margin: 0 auto 16px !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 2.8rem !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 2.3rem !important;
  }
`;

const StyledHighlight = styled.span`
  display: block;
  font-size: 4rem;
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.primary};
  text-align: center;

  @media (max-width: 768px) {
    font-size: 2.8rem;
  }
`;

const StyledSubtitle = styled(Paragraph)`
  && {
    color: ${({ theme }) => theme.palette.text.heading};
    font-size: 1.4rem;
    font-weight: 400;
    letter-spacing: 0.01em;
    line-height: 1.35;
    max-width: 720px;
    text-align: center;
    margin: 0 auto 40px !important;

    @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
      font-size: 1rem;
      margin-bottom: 24px !important;
    }
    @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      font-size: 1rem !important;
      max-width: 330px;
    }
  }
`;

const StyledButtonRow = styled.div`
  display: flex;
  gap: 18px;
  justify-content: center;
  flex-wrap: wrap;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    flex-direction: column;
  }
`;

const StyledCenterSection = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
`;
const StyledPrimaryButton = styled(Button)`
  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
  color: ${({ theme }) => theme.palette.common.white} !important;
  font-weight: 500 !important;
  font-size: 16px !important;
  padding: 16px 32px !important;
  min-width: 248px;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow} !important;

  &:hover {
    background: linear-gradient(90deg, #a839ff 0%, #377dff 100%) !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    padding: 14px 32px !important;
    height: 42px !important;
  }
`;

const StyledSecondaryButton = styled(Button)`
  border: 1.5px solid ${({ theme }) => theme.border.color} !important;
  font-weight: 600 !important;
  font-size: 16px !important;
  padding: 16px 32px !important;
  min-width: 205px;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow} !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  gap: 8px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    padding: 14px 32px !important;
    height: 42px !important;
  }
`;

export {
  StyledButtonRow,
  StyledCenterSection,
  StyledHeading,
  StyledHighlight,
  StyledPillTag,
  StyledPrimaryButton,
  StyledSecondaryButton,
  StyledSubtitle,
};
