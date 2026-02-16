import React, { ReactNode } from 'react';
import { Drawer, DrawerProps } from 'antd';
import styled, { useTheme } from 'styled-components';
import AppLoader from '../../common/AppLoader';
import clsx from 'clsx';
import { useMediaQuery } from 'react-responsive';
import { CloseOutlined } from '@ant-design/icons';
import { useInfoViewContext } from '@unpod/providers';

export const StyledDrawer = styled(Drawer as any)`
  /*& .ant-drawer-wrapper-body {
    width: 320px !important;

    @media (min-width: ${({ theme }) => theme.breakpoints.sm}px) {
      width: 450px !important;
    }

    @media (min-width: ${({ theme }) => theme.breakpoints.xl}px) {
      width: 550px !important;
    }

    @media (min-width: ${({ theme }) => theme.breakpoints.xxl}px) {
      width: 650px !important;
    }
  }

  &.full-width-view .ant-drawer-wrapper-body {
    width: 95% !important;
  }

  &.medium-view .ant-drawer-wrapper-body {
    @media screen and (min-width: ${({ theme }) => theme.breakpoints.sm}px) {
      width: 50% !important;
    }
  }

  &.large-view .ant-drawer-wrapper-body {
    @media screen and (min-width: ${({ theme }) => theme.breakpoints.sm}px) {
      width: 90% !important;
    }
  }*/

  .transparent & {
    margin-top: 56px;
    height: calc(100% - 56px) !important;
  }

  & .ant-drawer-header {
    padding: 16px 24px;

    .ant-drawer-header-title {
      flex-direction: row-reverse;
    }
  }

  & .ant-drawer-body {
    padding: 24px 24px 0;
  }

  & .ant-drawer-title {
    font-size: 16px;
    color: ${({ theme }) => theme.palette.text.heading};
    font-weight: ${({ theme }) => theme.font.weight.bold};

    @media (min-width: ${({ theme }) => theme.breakpoints.xxl}px) {
      font-size: 18px;
    }

    @media (min-width: ${({ theme }) => theme.breakpoints.xxl + 320}px) {
      font-size: 20px;
    }
  }

  & .inner-container {
    padding-top: 5px;
    overflow: hidden;
  }

  & .ant-drawer-footer {
    padding: 10px 24px;

    & .ant-btn {
      min-width: 120px;

      &:not(:first-child) {
        margin-left: 10px;
      }
    }
  }
`;

type AppDrawerProps = DrawerProps & {
  className?: string;
  fullWidth?: boolean;
  title?: ReactNode;
  showLoader?: boolean;
  children: ReactNode;
  loading?: boolean;
  padding?: string | number;
  placement?: 'right' | 'left' | 'top' | 'bottom';
  closable?: boolean;
  hideTransparent?: boolean;
  isTabDrawer?: boolean;
  isCallFilterView?: boolean;
  overflowY?: 'auto' | 'hidden' | 'scroll' | 'visible';
  [key: string]: unknown;};

export const AppDrawer: React.FC<AppDrawerProps> = ({
  className = '',
  fullWidth = false,
  title,
  showLoader = false,
  children,
  loading,
  padding,
  placement = 'right',
  closable = false,
  isTabDrawer = false,
  isCallFilterView = false,
  overflowY,
  width,
  ...restProps
}) => {
  const { loading: innerLoading } = useInfoViewContext();
  const theme = useTheme();
  const isSm = useMediaQuery({ minWidth: theme.breakpoints.sm });
  const isXl = useMediaQuery({ minWidth: theme.breakpoints.xl });
  const isSXll = useMediaQuery({ minWidth: theme.breakpoints.xxl });

  let drawerWidth: string | number = width || 378;
  const isMediumView = className.includes('medium-view');
  const isLargeView = className.includes('large-view');

  if (!width) {
    if (isSm) {
      drawerWidth = 450;
    }

    if (isXl) {
      drawerWidth = 550;
    }

    if (isSXll) {
      drawerWidth = 650;
    }
  }

  if (isMediumView) {
    drawerWidth = '50%';
  }

  if (isLargeView) {
    drawerWidth = '90%';
  }

  if (fullWidth) {
    drawerWidth = '95%';
  }

  return (
    <Drawer
      placement={placement}
      rootClassName={clsx('app-drawer', className)}
      title={title ? <div className={'mi-header'}>{title}</div> : null}
      size={drawerWidth}
      closable={closable}
      destroyOnHidden={true}
      closeIcon={<CloseOutlined mi-role={'close'} />}
      {...restProps}
      styles={{
        body: {
          scrollbarWidth: 'thin',
          padding: padding
            ? padding
            : isTabDrawer
              ? '16px 0 6px 24px'
              : isCallFilterView
                ? '0 16px 0px 24px'
                : title
                  ? '24px'
                  : '0px',
          overflowY: overflowY ? overflowY : 'auto',
        },
      }}
    >
      {children}
      {showLoader && (innerLoading || loading) && (
        <AppLoader position="absolute" />
      )}
    </Drawer>
  );
};

export default AppDrawer;
