'use client';
import styled from 'styled-components';
import { Button, Card, Typography } from 'antd';

const { Paragraph } = Typography;

export const StyledCard = styled(Card)`
  border-radius: 8px;
  border: 0 !important;
  background: rgba(255, 255, 255, 0.12) !important;

  @media screen and (min-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 800px !important;
    max-height: 600px !important;
    text-align: center !important;
    margin-inline: auto !important;
    overflow: hidden !important;
    overflow-y: auto !important;
  }

  @media screen and (min-width: ${({ theme }) => theme.breakpoints.md}px) {
    padding: 0 !important;
  }
`;

export const StyledCardDescription = styled.div`
  font-size: 16px;
  font-weight: 600 !important;
  margin-bottom: 16px !important;
  text-align: center;
  color: ${({ theme }) => theme.palette.common.white};

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-bottom: 14px !important;
    font-size: 14px !important;
    margin-top: 16px;
  }
`;

export const StyledCardTitle = styled.div`
  font-size: 48px !important;
  font-weight: 700 !important;
  text-align: center;
  line-height: 1.2 !important;
  margin-bottom: 8px !important;
  color: ${({ theme }) => theme.palette.common.white};

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 40px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 72px !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 42px !important;
    margin: 0 !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 26px !important;
  }
`;

export const StyledParagraph = styled(Paragraph)`
  font-size: 0.875em;
  color: ${({ theme }) => theme.palette.common.white};
  max-width: 768px !important;
  margin-inline: auto !important;
  text-align: center;
  margin-top: 8px !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 12px !important;
    margin-top: 16px !important;
  }
`;

export const StyledCardBody = styled.div`
  //height: 350px;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    justify-content: center !important;
    text-align: center !important;
  }
`;

export const StyledPrimaryButton = styled(Button)`
  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
  color: ${({ theme }) => theme.palette.common.white} !important;
  font-weight: 500 !important;
  font-size: 16px !important;
  padding: 8px 16px !important;
  max-width: 200px;
  margin-inline: auto;

  &:hover {
    background: linear-gradient(90deg, #a839ff 0%, #377dff 100%) !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    padding: 14px 32px !important;
    height: 42px !important;
    max-width: 250px !important;
  }
`;
