import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
`;

export const StyledGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
`;
