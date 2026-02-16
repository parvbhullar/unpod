import styled from 'styled-components';

export const StyledContainer = styled.div`
  @media (max-width: ${({ theme }) => theme.breakpoints.lg + 140}px) {
    margin-block: 0;
  }
`;

export const StyledListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px 16px;
  align-items: stretch;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg + 140}px) {
    gap: 16px 5px;
  }

  & > * {
    min-height: 400px;
  }
`;
