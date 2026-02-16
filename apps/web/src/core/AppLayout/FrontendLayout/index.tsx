'use client';
import { StyledLayout } from './index.styled';
import { Layout } from 'antd';
import AppInfoView from '@unpod/components/common/AppInfoView';
import { AppOrgContextProvider, useAuthContext } from '@unpod/providers';

import LayoutHeader from './LayoutHeader';
import LayoutFooter from './LayoutFooter';
import type { LayoutProps } from '@/types/common';

const { Content } = Layout;

type FrontendLayoutProps = LayoutProps & {
  headerBg?: string;
};

const LayoutComponent = ({ headerBg, children }: FrontendLayoutProps) => {
  const { isAuthenticated } = useAuthContext();

  return (
    <StyledLayout>
      <LayoutHeader headerBg={headerBg} />
      <Content className="main-content">{children}</Content>
      <LayoutFooter />
      {isAuthenticated && <AppInfoView />}
    </StyledLayout>
  );
};

const FrontendLayout = (props: FrontendLayoutProps) => {
  return (
    <AppOrgContextProvider>
      <LayoutComponent {...props} />
    </AppOrgContextProvider>
  );
};

export default FrontendLayout;
