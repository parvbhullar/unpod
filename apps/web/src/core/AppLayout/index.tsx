import { Fragment } from 'react';
import type { LayoutProps } from '@/types/common';
// import { useAuthContext } from '@unpod/providers';
// import AppLoader from '@unpod/components/AppLoader';
// import AuthLayout from './AuthLayout';
// import MainLayout from './MainLayout';

type AppLayoutProps = LayoutProps & {
  headerProps?: Record<string, unknown>;
  isPublicView?: boolean;
};

const AppLayout = (props: AppLayoutProps) => {
  // const { isAuthenticated, isLoading,  } = useAuthContext();
  return (
    <Fragment>
      {props.children}
      {/*{isLoading && <AppLoader />}

      {isAuthenticated || props?.isPublicView ? (
        <MainLayout {...props} />
      ) : (
        <AuthLayout {...props} />
      )}*/}
    </Fragment>
  );
};

export default AppLayout;
