import styled from 'styled-components';

export const StyledRoot = styled.div`
  height: calc(100vh - 10px);
  position: relative;
  overflow: hidden;
  display: flex;
  gap: 5px;
`;

export const StyledMainContent = styled.div`
  flex: 1;
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius}
    ${({theme}) => theme.component.card.borderRadius} 0 0;
  overflow-y: auto;
`;

export const StyledContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  min-height: 100%;
`;
