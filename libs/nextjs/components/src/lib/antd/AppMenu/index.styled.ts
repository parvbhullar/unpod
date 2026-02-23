import styled from 'styled-components';

export const StyledMenuContainer = styled.div`
  position: relative;
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledOverlayLoader = styled.div`
  position: absolute !important;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.4);
  z-index: 1000;
`;

export const StyledOverlayLoaderText = styled.div`
  margin-top: 25%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
`;
