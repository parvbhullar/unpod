'use client';

import { StyledMainContent, StyledRoot } from './index.styled';
import AppModuleContextProvider from '@unpod/providers/AppModuleContextProvider';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppSidebarDrawer from '@unpod/components/antd/AppDrawer/AppSidebarDrawer';
import {
  useAppPageLayoutActionsContext,
  useAppPageLayoutContext,
} from '@/core/AppLayout/PageContentLayout/AppPageLayourContext';
import { useAppSpaceContext } from '@unpod/providers';
import type { LayoutProps } from '@/types/common';
import type { ReactNode } from 'react';

type PageContentLayoutProps = LayoutProps & {
  sidebar: ReactNode;
  type?: 'bridge' | 'agent';
};

const PageContentLayout = ({
  sidebar,
  type = 'bridge',
  children,
}: PageContentLayoutProps) => {
  const { isMobileView } = useAppPageLayoutContext();
  const { activeTab } = useAppSpaceContext();
  console.log('activeTab in PageContentLayout', activeTab);
  const { sidebarWidth, isDrawerOpened } = useAppPageLayoutContext();
  const { setInDrawerOpen } = useAppPageLayoutActionsContext();
  if (activeTab === 'logs' || activeTab === 'analytics') {
    return (
      <AppModuleContextProvider type={type}>
        <AppPageContainer>
          <StyledRoot>
            <StyledMainContent>{children}</StyledMainContent>
          </StyledRoot>
        </AppPageContainer>
      </AppModuleContextProvider>
    );
  }
  return (
    <AppModuleContextProvider type={type}>
      <AppPageContainer>
        <StyledRoot>
          {isMobileView ? (
            <AppSidebarDrawer
              isDrawerOpened={isDrawerOpened}
              setInDrawerOpen={setInDrawerOpen}
              sidebarWidth={sidebarWidth}
            >
              {sidebar}
            </AppSidebarDrawer>
          ) : (
            sidebar
          )}
          <StyledMainContent>{children}</StyledMainContent>
        </StyledRoot>
      </AppPageContainer>
    </AppModuleContextProvider>
  );
};

export default PageContentLayout;
