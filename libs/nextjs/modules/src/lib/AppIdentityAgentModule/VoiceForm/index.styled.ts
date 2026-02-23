import styled from 'styled-components';

export const StyledItemRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
`;
export const StyledMainContainer = styled.div`
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto !important;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    width: 100%;
  }
`;
