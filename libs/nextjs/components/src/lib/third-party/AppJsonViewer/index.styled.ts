import styled from 'styled-components';

export const StyledCopyWrapper = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  bottom: auto;
  left: auto;
  z-index: 1;
  opacity: 0;
  transition: opacity 0.3s;
`;

export const StyledContainer = styled.div`
  position: relative;
  background: ${({theme}) => theme.palette.background.component};
  padding: 12px;
  overflow-x: auto;
  max-width: 100%;

  & pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  &:hover ${StyledCopyWrapper} {
    opacity: 1;
  }
`;
