import styled from 'styled-components';

export const StyledContainer = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
`;

export const StyledListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  grid-gap: 20px;
`;

export const StyledClientBox = styled.div`
  position: relative;
  display: flex;
  justify-content: center;
  width: 80px;
  height: 80px;
`;
