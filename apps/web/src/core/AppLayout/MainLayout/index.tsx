'use client';
import { StyledLayout, StyledMain } from './index.styled';
import {
  AppOrgContextProvider,
  useTourActionsContext,
  useTourContext,
} from '@unpod/providers';
import AppInfoView from '@unpod/components/common/AppInfoView';
import { OnboardingTour } from '@unpod/components';
import type { LayoutProps } from '@/types/common';

type MainLayoutProps = LayoutProps & {
  headerProps?: Record<string, unknown>;
  noLayout?: boolean;
};

const MainLayoutComponent = ({ children, noLayout }: MainLayoutProps) => {
  return noLayout ? (
    children
  ) : (
    <StyledLayout>
      <StyledMain>{children}</StyledMain>
    </StyledLayout>
  );
};

const TourWrapper = () => {
  const { showTour } = useTourContext();
  const { completeTour } = useTourActionsContext();
  return <OnboardingTour isOpen={showTour} onComplete={completeTour} />;
};

const MainContentLayout = (props: MainLayoutProps) => {
  return (
    <AppOrgContextProvider>
      <MainLayoutComponent {...props} />
      <TourWrapper />
      <AppInfoView hideLoader />
    </AppOrgContextProvider>
  );
};

export default MainContentLayout;
