import styled from 'styled-components';

export const StyledContainer = styled.div`
  width: 100%;
  margin: 0 0 0 44px;
  padding: 0 20px;
`;

export const StyledSourceList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  max-width: calc(100% - 88px);
`;
