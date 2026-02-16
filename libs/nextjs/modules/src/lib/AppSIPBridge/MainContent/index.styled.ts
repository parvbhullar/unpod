import styled from 'styled-components';

export const StyledRoot = styled.div`
  flex: 1;
  height: calc(100vh - 10px);
  overflow-y: hidden;
  display: flex;
  flex-direction: column;
  position: relative;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: calc(100vh - 85px);
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    height: calc(100vh - 20px);
  }

  @media (max-width: 768px) {
    .ant-tabs-content {
      padding: 0 !important;
    }
`;

export const StyledTabsWrapper = styled.div`
  overflow: auto;
  display: flex;
  flex-direction: column;
  scrollbar-width: thin;

  .ant-tabs-nav {
    position: sticky;
    top: 0;
    background: #fff;
    z-index: 10;
  }

  .ant-tabs-content-holder {
    flex: 1;
    overflow-y: auto;
    padding: 0 32px;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      padding: 0 10px;
    }
  }
  .ant-tabs-top > .ant-tabs-nav {
    margin: 0 !important;
  }

  .ant-tabs-nav {
    padding: 0 32px;

    @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
      padding: 0 10px;
    }
  }
`;
