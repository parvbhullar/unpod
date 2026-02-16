'use client';
import styled from 'styled-components';
import { Button, Card, Typography } from 'antd';

const { Title } = Typography;

const StyledTitle = styled(Title)`
  font-size: 48px !important;
  font-weight: 700 !important;
  margin-bottom: 16px !important;
  color: ${({ theme }) => theme.palette.common.white} !important;
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
  color: ${({ theme }) => theme.palette.common.white} !important;
  margin-bottom: 40px !important;
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
  border: 0px !important;
  background: ${({ theme }) => theme.palette.background.default} !important;
  transition: all 300ms ease;

  &:hover {
    box-shadow: ${({ theme }) => theme.component.card.boxShadow};
    transform: scale(1.05);
  }

  @media screen and (min-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 650px !important;
    text-align: center !important;
    margin-inline: auto !important;
  }

  ,
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    padding: 0px !important;
    shadow: 0px 1px 2px rgba(255, 255, 255, 0.2) !important;
  }
`;

const StyledCardDescription = styled.div`
  font-size: 16px !important;
  font-weight: 600 !important;
  max-width: 560px !important;
  margin-inline: auto !important;
  margin-bottom: 16px !important;
  text-align: center;
  color: ${({ theme }) => theme.palette.text.heading} !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 14px !important;
    max-width: 250px !important;
    margin-bottom: 24px !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    justify-content: center !important;
    margin-bottom: 14px !important;
  }
  @media screen and (min-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    justify-content: center !important;
    margin-bottom: 14px !important;
  }
`;

const StyledNumber = styled.a`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 35px;
  color: ${({ theme }) => theme.palette.primary};
  text-decoration: none;
  font-weight: 500;
  padding: 12px 24px;
  margin: 20px auto;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  max-width: fit-content;

  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(0, 0, 0, 0.2);
  }

  svg {
    margin-left: 4px;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 30px;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 24px;
    padding: 18px !important;
  }
`;

const StyledCardBody = styled.div`
  height: 350px;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  overflow: hidden;
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    height: 340px;
    padding: 0px !important;
    flex-direction: column;
    justify-content: center !important;
    text-align: center !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: 300px;
    padding: 0px !important;
    flex-direction: column;
    justify-content: center !important;
    text-align: center !important;
  }
`;

const StyledPrimaryButton = styled(Button)`
  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
  color: ${({ theme }) => theme.palette.common.white} !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  margin: 0 auto;

  &:hover {
    background: linear-gradient(90deg, #a839ff 0%, #377dff 100%) !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 14px !important;
    padding: 14px 32px !important;
    height: 42px !important;
    max-width: 250px !important;
    margin-top: 16px !important;
  }
`;

const StyledCardIcon = styled.div`
  background: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.common.white};
  width: 50px;
  height: 50px;
  padding: 8px;
  border-radius: 50%;
  margin-left: 16px;
  display: flex;
  justify-content: center;
  align-items: center;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 40px;
    height: 40px;
    padding: 4px;
    border-radius: 50%;
    margin-left: 8px;
  }
`;

export {
  StyledTitle,
  StyledSubTitle,
  StyledCard,
  StyledCardDescription,
  StyledCardBody,
  StyledNumber,
  StyledPrimaryButton,
  StyledCardIcon,
};
