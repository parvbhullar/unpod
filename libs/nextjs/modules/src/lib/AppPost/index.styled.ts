import styled from 'styled-components';

export const StyledContainer = styled.div`
  //position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  width: 100%;
  background-color: ${({theme}) => theme.palette.background.default};
`;

export const StyledContent = styled.div<{ overFlowHidden?: boolean }>`
  scrollbar-width: thin;
  height: calc(100vh - 240px);
  overflow: ${({overFlowHidden}) => (overFlowHidden ? 'hidden' : 'auto')};
`;

export const StyledDetailsRoot = styled.div`
  width: 100%;
  max-width: calc(${({theme}) => theme.sizes.mainContentWidth});
  background-color: ${({theme}) => theme.palette.background.default};
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;
`;
export const StyledPostHeader = styled.div`
  width: 100%;
  max-width: calc(${({theme}) => theme.sizes.mainContentWidth});
  margin: 0 auto;
`;

export const StyledMoreContainer = styled.div`
  display: flex;
  justify-content: center;
  padding-top: 24px;
`;

export const StyledNoAccessContainer = styled.div`
  margin: 16px auto;
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
`;

export const VoiceOverlay = styled.div<{ show?: boolean }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 204px !important;
  background: ${({theme}) => theme.palette.background.default};
  //border-radius: 50%;

  overflow-y: hidden;

  opacity: ${(props) => (props.show ? 1 : 0)};
  transform: scale(${(props) => (props.show ? 1 : 0.95)});
  transition: all 0.3s ease;

  pointer-events: auto;
`;
