import styled from 'styled-components';

export const StyledContainer = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  padding: 0 24px;
  height: calc(100vh - 74px);
  overflow-y: auto;
`;

export const StyledInnerContainer = styled.div`
  max-width: ${({ theme }) => theme.sizes.mainContentWidth};
  margin: 0 auto;
  padding: 24px 0;
  position: relative;
`;
