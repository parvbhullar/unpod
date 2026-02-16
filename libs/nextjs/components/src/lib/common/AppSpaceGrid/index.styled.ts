import styled from 'styled-components';

export const StyledRoot = styled.div`
  width: 100%;
  max-width: 1250px;
  margin: 0 auto;
`;

export const StyledGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
`;
