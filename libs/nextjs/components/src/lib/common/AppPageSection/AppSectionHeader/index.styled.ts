'use client';
import styled from 'styled-components';

export const StyledSectionHeader = styled.div<{ $maxWidth?: number }>`
  margin: 0 auto;
  max-width: ${({$maxWidth}) => ($maxWidth ? `${$maxWidth}px` : '100%')};
  text-align: center;
  padding-bottom: 32px;

  .sub-title {
    margin-top: 0 !important;
    font-weight: 400;
    color: ${({theme}) => theme.palette.text.primary};
  }
`;

export const StyledExtraWrapper = styled.div`
  margin: 24px auto 0;
  max-width: 550px;
  text-align: center;
`;
