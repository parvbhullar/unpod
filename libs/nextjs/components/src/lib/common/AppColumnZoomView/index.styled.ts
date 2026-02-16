import styled from 'styled-components';

export const StyledRootContainer = styled.div`
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

export const StyledCopyWrapper = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  bottom: auto;
  left: auto;
  z-index: 1;
  opacity: 0;
  background: ${({ theme }) => theme.palette.background.component};
  border-radius: ${({ theme }) => theme.radius.circle};
  transition: opacity 0.3s;
`;

export const StyledFullContent = styled(StyledRootContainer)`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: ${({ theme }) => theme.palette.background.default};

  &:hover ${StyledCopyWrapper} {
    opacity: 1;
  }
`;

export const StyledContentContainer = styled.div`
  padding: 16px;
  height: 100%;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  position: relative;
  overflow: hidden;

  &.json-content {
    background: ${({ theme }) => theme.palette.background.component};
  }

  & pre {
    overflow: visible;
  }
`;

export const StyledTitleContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
`;

export const StyledContentWrapper = styled.div`
  overflow-y: auto;
  height: 100%;
  font-size: 16px;
  line-height: 1.6;

  /*font-family: ${({ theme }) => theme.font.family};
  font-size: 16px;
  line-height: 1.6;
  color: ${({ theme }) => theme.palette.text.content};

  & ol,
  & ul,
  & dl {
    margin: 0;
    padding: 0 0 12px 20px;
  }*/
`;

export const StyledDocWrapper = styled.div`
  overflow-y: auto;
  height: 100%;
`;

export const StyledIframeContainer = styled.div`
  height: 100%;
  border: 1px solid ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  overflow: hidden;
`;
