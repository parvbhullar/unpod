'use client';
import styled from 'styled-components';

export const StylesImageWrapper = styled.div`
  width: 110px;
  height: 110px;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const StyledInputWrapper = styled.div`
  flex: 1;
`;

export const StyledItemWrapper = styled.div`
  display: flex;
  gap: 24px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    gap: 12px;
  }
`;
