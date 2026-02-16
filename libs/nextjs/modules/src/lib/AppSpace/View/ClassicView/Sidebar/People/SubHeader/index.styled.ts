import styled from 'styled-components';
import { Space, Tabs } from 'antd';

export const StyledRoot = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px 7px 10px;
  border-bottom: 1px solid ${({ theme }) => theme.border.color};
  background-color: ${({ theme }) => theme.palette.background.default};
  z-index: 2;
`;

export const StyledSearchBoxWrapper = styled.div`
  width: 230px !important;
`;

export const StyledContent = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
`;

export const StyledSpace = styled(Space)`
  align-items: flex-end;
  .ant-btn-text {
    color: ${({ theme }) => theme.palette.text.secondary};
    &:hover,
    &.active {
      color: ${({ theme }) => theme.palette.primary};
    }
  }
`;

export const StyledTabs = styled(Tabs)`
  background-color: ${({ theme }) => theme.palette.background.default};
  position: sticky;
  top: 0;
  z-index: 1;
  padding-inline: 12px 10px;

  .ant-tabs-nav {
    margin-bottom: 0;
  }

  .ant-tabs-nav-operations {
    display: none !important;
  }

  .ant-tabs-extra-content {
    padding-left: 8px;
  }

  .ant-tabs-nav-more {
    margin-left: 0 !important;
  }
`;

export const StyledFilterContent = styled.div`
  opacity: 0;
  height: 0;
  overflow: hidden !important;
  transform: translateY(-50px);
  transition: all 0.3s ease;
  z-index: 1;

  &.active {
    opacity: 1;
    height: calc(-129px + 100vh);
    overflow-y: auto;
    transform: translateX(0);
  }
`;

export const StyledFilterBar = styled.div`
  margin-left: auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px solid ${({ theme }) => theme.border.color};

  padding: 4px 8px;
  //width: 50px;
`;
