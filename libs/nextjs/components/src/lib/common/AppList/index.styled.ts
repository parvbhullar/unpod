import styled from 'styled-components';

export const StyledScrollViewport = styled.div`
  width: 100%;
  overflow-y: auto;
  scrollbar-width: thin;
`;

type StyledContentWrapperProps = {
  $maxWidth?: string | number;
  $padding?: string | number;};

export const StyledContentWrapper = styled.div<StyledContentWrapperProps>`
  width: 100%;
  max-width: ${({ theme, $maxWidth }) =>
    $maxWidth ? $maxWidth : theme.sizes.mainContentWidth};
  padding: ${({ $padding }) => ($padding ? $padding : 0)};
  display: flex;
  flex-direction: column;

  margin: 0 auto;
`;

export const StyledListContainer = styled.div`
  width: 100%;
  display: flex;
  flex-direction: column;
`;

export const StyledEmptyListContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  min-height: 450px;
  height: 100%;
`;

export const StyledEmptyListContainerFlex = styled(StyledEmptyListContainer)`
  flex-direction: row;
  opacity: 0;
  animation: fadeIn 0.5s ease-in-out 0.2s forwards;
  font-size: ${({ theme }) => theme.font.size.base};
  color: ${({ theme }) => theme.palette.text.primary};
  padding: 20px;
  & h4 {
    font-size: 18px;
    color: ${({ theme }) => theme.palette.text.secondary};
    margin-bottom: 12px;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`;

export const StyledListFooter = styled.div`
  padding: 10px;
  z-index: 11;
  background-color: ${({ theme }) =>
    theme.palette.background.paper
      ? `${theme.palette.background.paper}80`
      : 'rgba(255, 255, 255, 0.5)'};
  backdrop-filter: blur(6px);
  color: ${({ theme }) => theme.palette.text.secondary};
  display: flex;
  justify-content: center;
  opacity: 0;
  animation: fadeIn 0.5s ease-in-out 2s forwards;

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`;

export const StyledRecordCount = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px;
  background-color: ${({ theme }) =>
    theme.palette.background.paper
      ? `${theme.palette.background.paper}80`
      : 'rgba(255, 255, 255, 0.5)'};
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  color: ${({ theme }) => theme.palette.text.secondary};
  font-size: ${({ theme }) => theme.font.size.sm};
  z-index: 10;
`;

export const StyledLoaderProgress = styled.div`
  width: 100%;
  display: flex;
  justify-content: center;
  color: ${({ theme }) => theme.palette.text.secondary};
  padding: 8px;

  box-sizing: border-box;

  & span {
    margin-left: 8px;

    [dir='rtl'] & {
      margin-left: 0;
      margin-right: 8px;
    }
  }
`;

export const StyledLoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.5);
  z-index: 10;
`;
