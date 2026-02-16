import styled from 'styled-components';

export const StyledContainer = styled.div`
  margin: 16px auto 0 auto;
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin-top: 0;
  }
`;
