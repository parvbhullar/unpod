'use client';

import styled from 'styled-components';

export const StyledGrid = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  max-width: 100%;
  width: 600px;
  margin: 0 auto;

  & > * {
    flex: 1 1 calc(50% - 16px);
    width: calc(50% - 16px);
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    & > * {
      flex: 1 1 100%;
      width: 100%;
    }
  }
`;
