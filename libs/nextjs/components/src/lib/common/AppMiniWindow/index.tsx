'use client';
import React, { ReactNode, useState } from 'react';
import { Space } from 'antd';
import { MdClear } from 'react-icons/md';
import { CgMinimizeAlt } from 'react-icons/cg';
import { FiMaximize2 } from 'react-icons/fi';
import {
  StyledAppDrawer,
  StyledBody,
  StyledFooter,
  StyledWrapper,
} from './index.styled';
import { useMediaQuery } from 'react-responsive';
import AppLoader from '../AppLoader';
import { MobileWidthQuery } from '@unpod/constants';
import { DrawerProps } from 'antd/es/drawer';

type AppMiniWindowProps = Omit<DrawerProps, 'closable'> & {
  open: boolean;
  creatingPost?: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  openLocally?: boolean;
  closable?: boolean;};

const AppMiniWindow: React.FC<AppMiniWindowProps> = ({
  open,
  title,
  onClose,
  children,
  creatingPost,
  openLocally,
  ...restProps
}) => {
  const [maximize, setMaximize] = useState(false);
  const desktopScreen = useMediaQuery({ query: '(min-width: 1366px)' });
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  const onMaximize = () => {
    setMaximize(!maximize);
  };
  const onMinimize = () => {
    setMaximize(!maximize);
  };

  const getHeight = () => {
    if (maximize) {
      return openLocally ? 'calc(100% - 10px)' : '100%';
    }
    return desktopScreen ? 550 : 480;
  };
  const getStyle = () => {
    if (mobileScreen) {
      return {
        right: 5,
        left: 5,
        borderRadius: 0,
        margin: '0 auto',
        width: '96%',
      };
    } else {
      if (openLocally) {
        return {
          borderRadius: '8px 8px 0 0',
          width: 'calc(100% - 20px)',
          left: 10,
          right: 10,
        };
      }
      return {
        minWidth: maximize ? '50%' : 380,
        maxWidth: maximize ? '70%' : 600,
        right: 20,
        borderRadius: '8px 8px 0 0',
        width: '90%',
      };
    }
  };

  return (
    <StyledAppDrawer
      title={title}
      open={open}
      onClose={onClose}
      closable={false}
      getContainer={openLocally ? false : undefined}
      className="app-mini-window"
      height={getHeight()}
      rootStyle={{
        position: 'absolute',
        maxWidth: openLocally ? 'calc(100% - 10px)' : '100%',
        ...getStyle(),
      }}
      // maskStyle={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}
      //  styles={{
      //             wrapper: { boxShadow: 'none', maxHeight: '100%' }}}
      // bodyStyle={{ padding: 0 }}
      styles={{
        body: { padding: 0 },
        mask: { backgroundColor: 'rgba(0, 0, 0, 0.2)' },
        wrapper: { boxShadow: 'none', maxHeight: '100%' },
      }}
      placement="bottom"
      extra={
        <Space size="middle">
          {maximize ? (
            <CgMinimizeAlt
              fontSize={20}
              style={{ cursor: 'pointer' }}
              onClick={onMinimize}
            />
          ) : (
            <FiMaximize2
              fontSize={20}
              style={{ cursor: 'pointer' }}
              onClick={onMaximize}
            />
          )}
          <MdClear
            fontSize={18}
            style={{ cursor: 'pointer' }}
            onClick={onClose}
          />
        </Space>
      }
      {...restProps}
    >
      <StyledWrapper>{children}</StyledWrapper>
      {creatingPost && <AppLoader position="absolute" />}
    </StyledAppDrawer>
  );
};

export default AppMiniWindow;

type AppMiniWindowBodyProps = {
  children: ReactNode;};

export const AppMiniWindowBody: React.FC<AppMiniWindowBodyProps> = (props) => (
  <StyledBody {...props} />
);

type AppMiniWindowFooterProps = {
  children: ReactNode;};
export const AppMiniWindowFooter: React.FC<AppMiniWindowFooterProps> = (
  props,
) => <StyledFooter {...props} />;
