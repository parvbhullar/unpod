import { StyledLayout } from './index.styled';
import AppInfoView from '@unpod/components/common/AppInfoView';
import LayoutHeader from './LayoutHeader';
import type { LayoutProps } from '@/types/common';

const AuthLayout = ({ children }: LayoutProps) => {
  return (
    <StyledLayout>
      <LayoutHeader />
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {children}
      </div>
      <AppInfoView />
    </StyledLayout>
  );
};

export default AuthLayout;
