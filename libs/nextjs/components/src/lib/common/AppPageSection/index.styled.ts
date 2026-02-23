'use client';
import styled from 'styled-components';

export const StyledSection = styled.div<{ $bgColor?: string }>`
  padding: 80px 0;
  background-color: ${({$bgColor}) => $bgColor};

  @media screen and (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    padding: 40px 0;
  }
`;

export const StyledContainer = styled.div`
  margin: 0 auto;
  max-width: 1280px;
  padding: 0 50px;

  @media screen and (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    padding: 0 30px;
  }

  @media screen and (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 0 14px;
  }
`;
