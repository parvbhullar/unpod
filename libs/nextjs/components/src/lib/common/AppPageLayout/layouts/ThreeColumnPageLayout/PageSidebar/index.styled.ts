import styled from 'styled-components';
import { Button, Layout, Menu, Skeleton } from 'antd';
import SimpleBar from 'simplebar-react';

const { Sider } = Layout;

export const StyledScrollbar = styled(SimpleBar)`
  height: 100%;

  & .simplebar-content {
    min-height: 100%;
    display: flex;
    flex-direction: column;
  }
`;

export const StyledLoadingContainer = styled.div`
  padding: 4px;
`;

export const StyledSkeletonButton = styled(Skeleton.Button)`
  margin-bottom: 8px;
`;

export const StyledMainMenu = styled(Menu)`
  border: 0 none !important;
  font-size: 13px;
  font-weight: 600;
  padding: 0;

  & .ant-menu-item {
    padding: 0 8px 0 4px !important;

    .ant-menu-item-icon {
      font-size: 18px;
    }
  }

  & .ant-menu-submenu {
    &.ant-menu-submenu-open .ant-menu-sub {
      margin-left: 20px;
      position: relative;
    }

    .ant-menu-submenu-title {
      padding-left: 4px !important;
      display: flex;
      align-items: center;

      &:hover,
      &.ant-menu-item-selected {
        color: ${({ theme }) => theme.palette.primary} !important;

        & .ant-menu-item-icon {
          color: ${({ theme }) => theme.palette.primary};
        }
      }

      .ant-menu-item-icon {
        font-size: 16px;
        vertical-align: -0.5em;
      }
    }
  }

  & .ant-menu-item-content {
    display: flex;
    flex: 1 !important;
    min-width: 0;
    align-items: center;
    justify-content: space-between;

    & .ant-menu-title {
      flex: 1;
      margin-right: 10px;
    }
  }

  & .ant-menu-item-group {
    .ant-menu-item-group-title {
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      box-shadow: 0 1px 5px rgba(0, 0, 0, 0.09);
    }
  }
`;

export const StyledAddBtnView = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 10px;
  position: sticky;
  bottom: 0;
  top: auto;
  margin: auto 0 0;
  background-color: ${({ theme }) => theme.palette.background.default};
`;

export const StyledAddBtn = styled(Button)`
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
`;

export const StyledSidebar = styled(Sider)<{ $hidePageHeader?: boolean }>`
  border-radius: ${({ theme }) =>
    `${theme.radius.base}px ${theme.radius.base}px ${theme.radius.base}px 0`};
  height: ${({ $hidePageHeader }) =>
    $hidePageHeader ? '100vh' : 'calc(100vh - 80px)'};
  overflow-y: auto;
  position: sticky !important;
  top: 64px;
  background-color: ${({ theme }) =>
    theme.palette.background.default} !important;
`;
