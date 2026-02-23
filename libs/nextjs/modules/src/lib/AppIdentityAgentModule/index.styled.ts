import styled from 'styled-components';

export const StyledRoot = styled.div`
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  flex: 1;
  height: calc(100vh - 10px);
  overflow-y: hidden;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    height: calc(100vh - 85px);
  }

  @media (max-width: ${({theme}) => theme.breakpoints.xs}px) {
    height: calc(100vh - 20px);
  }

  .ant-tabs-content {
    padding: 0 !important;
  }
`;

export const StyledTitleContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
`;

export const StyledContainer = styled.div`
  padding: 14px;
`;

export const StyledTabsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  scrollbar-width: thin;

  .ant-tabs-nav-wrap {
    width: ${({theme}) => theme.sizes.mainContentWidth};
    max-width: 100%;
    margin: 0 auto !important;
    flex: none !important;

    @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
      max-width: 100% !important;
    }
  }

  .ant-tabs-nav {
    position: sticky;
    top: 0;
    background: #fff;
    z-index: 10;
  }

  .ant-tabs-content-holder {
    flex: 1;
    width: 100% !important;
    padding-top: 14px !important;
  }

  .ant-tabs-top > .ant-tabs-nav {
    margin: 0 !important;
  }

  .ant-tabs-nav {
    padding: 0 14px;
  }
`;

export const StickyFooter = styled.div`
  position: sticky;
  bottom: 0;
  background: ${({theme}) => theme.palette.background.default};
  z-index: 99;
  width: ${({theme}) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto;
  padding-bottom: 14px;
`;

export const StyledTabRoot = styled.div`
  scrollbar-width: thin;
  height: calc(100vh - 225px);
  overflow: auto;
  padding: 14px !important;
`;
