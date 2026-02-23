'use client';
import styled from 'styled-components';

export const TagWrapper = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;

  @media (max-width: ${({theme}) => theme.breakpoints.xl}px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md + 52}px) {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
`;

export const TonePersonalityContainer = styled.div`
  margin-bottom: 12px;
`;
