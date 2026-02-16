import styled from 'styled-components';

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto 40px;
  position: relative;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  padding: 40px;
`;
