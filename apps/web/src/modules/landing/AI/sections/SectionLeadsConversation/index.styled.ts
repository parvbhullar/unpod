'use client';
import styled from 'styled-components';
import { Flex, Typography } from 'antd';
import { OnestFontFamily } from '../../index.styled';

const { Title, Paragraph } = Typography;

export const Container = styled.div`
  width: 100%;
`;

export const ContentWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
`;

export const StyledHeadContainer = styled(Flex)`
  padding: 0 1rem;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    flex-direction: column;
    text-align: center;
    align-items: center;
    padding: 0;
  }
`;

export const StyledTitle = styled(Title)`
  font-family: 'Oxanium', sans-serif;
  color: ${({ theme }) => theme.palette.text.heading} !important;
  font-size: 2rem !important;
  font-weight: 600;
  line-height: 1.2;
  max-width: 465px;
  width: 100%;
`;

export const ColoredText = styled.span`
  color: ${({ theme }) => theme.palette.primary};
`;

export const Description = styled(Paragraph)`
  font-size: 1.125rem;
  line-height: 1.6;
  color: ${({ theme }) => theme.palette.text.subheading};
  ${OnestFontFamily}
  font-weight: 400;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    font-size: 1rem;
    padding: 0;
  }
`;
export const StyledImageContainer = styled.div`
  position: relative;
  aspect-ratio: 995/498;
  width: 100%;
  margin-top: 42px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    aspect-ratio: 366 / 804;
  }
`;
