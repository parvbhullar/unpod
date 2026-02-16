'use client';
import styled, { css } from 'styled-components';
import { Flex, Typography } from 'antd';

const { Title } = Typography;

export const OnestFontFamily = css`
  font-family: 'Onest', sans-serif !important;
`;

export const StyledSubTitle = styled(Title)`
  ${OnestFontFamily}
  font-size : 20px !important;
  font-weight: 400 !important;
  margin: 0 auto !important;
  color: ${({ theme }) => theme.palette.text.subheading} !important;
  text-align: center;
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    font-size: 16px !important;
  }
`;

export const StyledTitle = styled(Title)`
  font-family: 'Oxanium', sans-serif;
  font-size: 42px !important;
  font-weight: 600 !important;
  margin-bottom: 6px !important;
  color: ${({ theme }) => theme.palette.text.heading} !important;

  & .text-active {
    color: ${({ theme }) => theme.palette.primary} !important;
  }

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    font-size: 38px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 34px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    font-size: 30px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 24px !important;
  }
`;

export const StyledFlex = styled(Flex)`
  gap: 50px;
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    gap: 10px;
  }
`;
