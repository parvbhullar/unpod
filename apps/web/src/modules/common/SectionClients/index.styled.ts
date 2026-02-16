import styled from 'styled-components';

export const StyledContainer = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
`;

export const StyledListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  grid-gap: 20px;
`;

export const StyledClientBox = styled.div`
  display: flex;
  justify-content: center;
`;
