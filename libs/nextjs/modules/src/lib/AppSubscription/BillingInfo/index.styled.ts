import styled from 'styled-components';

export const StyledContainer = styled.div`
  position: relative;
  padding: 8px 16px 16px 16px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  margin: 16px auto;
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    max-width: 100%;
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin: 0 auto;
  }
`;
