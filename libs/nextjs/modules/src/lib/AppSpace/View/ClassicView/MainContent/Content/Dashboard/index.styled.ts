import styled from 'styled-components';

export const StyledRoot = styled.div`
  flex: 1;
  height: calc(100vh - 74px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: ${({theme}) => theme.palette.common.white};
  scrollbar-width: thin;
`;

export const StyledCardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;
