import styled from 'styled-components';
import { Collapse } from 'antd';

const { Panel } = Collapse;

export const Container = styled.div`
  display: flex;
  background-color: ${({ theme }) => theme.palette.background.default};
`;

export const MainContent = styled.div`
  flex: 1;
  margin: 0 auto;
  overflow-y: hidden;
  height: 100vh;
  scrollbar-width: thin;
`;

export const StyledInnerContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: calc(100vh - 152px);
  overflow-y: auto;
`;

export const StyledRoot = styled.div`
  scrollbar-width: thin;
  height: calc(100vh - 90px);
  overflow: auto;
  display: flex;
  flex-direction: column;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: calc(100vh - 80px);
  }
`;

export const StyledMainContainer = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto !important;
  justify-content: center;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

export const CollapseWrapper = styled.div`
  .ant-collapse {
    background: ${({ theme }) => theme.palette.background.default} !important;
    border: none;
    overflow: hidden;
    padding: 14px;
  }

  .ant-collapse > .ant-collapse-item {
    margin-bottom: 16px;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid ${({ theme }) => theme.border.color};
  }

  .ant-collapse > .ant-collapse-item.ant-collapse-item-active {
    border: 1px solid ${({ theme }) => theme.palette.primary} !important;
  }

  .ant-collapse-header {
    align-items: center !important;
  }
`;

export const FooterBar = styled.div`
  position: sticky;
  bottom: 0;
  padding: 14px 14px 0;
  border-top: 1px solid ${({ theme }) => theme.border.color};
  display: flex;
  justify-content: flex-end;
  z-index: 10;
`;

export const StyledPanel = styled(Panel)`
  &.success {
    border: 1px solid ${({ theme }) => theme.palette.success} !important;
    border-radius: 12px !important;
  }
`;
