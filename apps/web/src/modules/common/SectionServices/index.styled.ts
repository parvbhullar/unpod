import styled from 'styled-components';

export const StyledContainer = styled.div`
  max-width: 100%;
  margin: 0 auto;
`;

export const StyledListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  grid-gap: 24px;
`;
