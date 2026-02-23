import styled from 'styled-components';

export const StyledRootWrapper = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  height: calc(100vh - 135px);
  overflow-y: auto;
  scrollbar-width: thin;
`;
export const StyledRoot = styled.div`
  width: 100%;
  max-width: calc(${({theme}) => theme.sizes.mainContentWidth});
  background-color: ${({theme}) => theme.palette.background.default};
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;
`;
