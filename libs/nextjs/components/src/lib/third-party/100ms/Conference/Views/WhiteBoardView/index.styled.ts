import styled from 'styled-components';

export const StyledContainer = styled.div`
  display: flex;
  width: 100%;
  height: 100%;
`;

export const StyledSidePaneContainer = styled.div`
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  flex: 0 0 20%;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    flex-direction: row;
    flex: 1 1 0;
  }
`;

export const StyledEditorRoot = styled.div`
  display: flex;
  margin-inline: 16px;
  flex: 3 1 0;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    flex: 2 1 0;

    & video {
      object-fit: contain;
    }
  }
`;

export const StyledEditorContainer = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
`;
