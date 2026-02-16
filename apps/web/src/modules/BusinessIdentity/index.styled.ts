import styled from 'styled-components';
import { Collapse } from 'antd';

const { Panel } = Collapse;

export const StyledRoot = styled.div`
  margin: 0 auto;
  min-height: 100vh;
  scrollbar-width: thin;
`;

export const StyledContainer = styled.div`
  padding: 24px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 0;
  }
`;

export const StyledInnerContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow-y: auto;
`;

export const StyledContent = styled.div`
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 0 auto !important;
  justify-content: center;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

export const StyledCollapse = styled(Collapse)`
  &.ant-collapse {
    background: ${({ theme }) => theme.palette.background.default};
    border: none;
    overflow: hidden;
    padding: 14px;
  }

  &.ant-collapse > .ant-collapse-item {
    margin-bottom: 16px;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid ${({ theme }) => theme.border.color};
  }

  &.ant-collapse > .ant-collapse-item.ant-collapse-item-active {
    border-color: ${({ theme }) => theme.palette.primary};
  }

  .ant-collapse-header {
    align-items: center !important;
  }
`;

export const StyledPanel = styled(Panel)`
  &.success {
    border-color: ${({ theme }) => theme.palette.success} !important;
  }
`;
