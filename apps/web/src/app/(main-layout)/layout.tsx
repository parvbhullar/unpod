import MainLayout from '@/core/AppLayout/MainLayout';
import LayoutSidebar from '@/core/AppLayout/MainLayout/LayoutSidebar';
import AppPageLayoutContextProvider from '@/core/AppLayout/PageContentLayout/AppPageLayourContext';
import {
  StyledContent,
  StyledLayoutMain,
} from '@/core/AppLayout/MainLayout/index.styled';
import { AppSpaceContextProvider } from '@unpod/providers';
import type { LayoutProps } from '@/types/common';

export default async function Layout({ children }: LayoutProps) {
  return (
    <MainLayout>
      <AppPageLayoutContextProvider sidebarWidth={320}>
        <AppSpaceContextProvider>
          <LayoutSidebar />
          <StyledLayoutMain>
            <StyledContent>{children}</StyledContent>
          </StyledLayoutMain>
        </AppSpaceContextProvider>
      </AppPageLayoutContextProvider>
    </MainLayout>
  );
}
