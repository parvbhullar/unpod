import React, {ReactNode} from 'react';
import {Drawer} from 'antd';
import styled from 'styled-components';

export const StyledDrawer = styled(Drawer as any)`
  .ant-drawer-body {
    padding: 0;
    background-color: ${({theme}) => theme.palette.background.default};
    border-radius: ${({theme}) => theme.component.card.borderRadius}
      ${({theme}) => theme.component.card.borderRadius} 0 0;
    display: flex;
    overflow: hidden;
    flex-direction: column;
    position: relative;
  }
`;

export type AppSidebarDrawerProps = {
  children: ReactNode;
  sidebarWidth?: number;
  isDrawerOpened: boolean;
  setInDrawerOpen: (open: boolean) => void;
};

export const AppSidebarDrawer: React.FC<AppSidebarDrawerProps> = ({
                                                                    children,
                                                                    sidebarWidth,
                                                                    isDrawerOpened,
                                                                    setInDrawerOpen,
                                                                  }) => {
  return (
    <StyledDrawer
      placement="left"
      title={null}
      destroyOnHidden={false}
      closeIcon={null}
      size={sidebarWidth || 320}
      open={isDrawerOpened}
      onClose={() => setInDrawerOpen(false)}
      maskClosable={true}
    >
      {children}
    </StyledDrawer>
  );
};

export default AppSidebarDrawer;
