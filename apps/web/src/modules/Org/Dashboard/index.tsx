'use client';
import React, { Fragment, useEffect } from 'react';
import { Typography } from 'antd';
import { DashboardSkeleton } from '@unpod/skeleton';
import { useAuthActionsContext, useAuthContext } from '@unpod/providers';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import PageHeader from '../detail/PageHeader';
import ProfileCard from './ProfileCard';
import { StyledCardContainer, StyledRoot } from './index.styled';
import { profiles } from './data';
import Metrics from './Metrics';
import { useIsDesktop } from '@unpod/custom-hooks';
import { useIntl } from 'react-intl';

const { Title } = Typography;

const Dashboard = () => {
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { formatMessage } = useIntl();

  const { isAuthenticated, user, isLoading, activeOrg } = useAuthContext();
  const { isDesktopApp } = useIsDesktop();
  useEffect(() => {
    if (activeOrg && isAuthenticated) {
      updateAuthUser({ ...user, active_organization: activeOrg });
      setActiveOrg(activeOrg);
    }
  }, [activeOrg, isAuthenticated]);

  return (
    <Fragment>
      <PageHeader pageTitle={activeOrg?.name} type="org" />

      <AppPageContainer>
        {isLoading ? (
          <DashboardSkeleton />
        ) : (
          <StyledRoot>
            <Title level={3}>
              {user
                ? `${formatMessage({ id: 'dashboard.welcomeUser' })}, ${user.first_name}`
                : `${formatMessage({ id: 'dashboard.welcomeGuest' })}`}
            </Title>

            <StyledCardContainer>
              {(
                profiles[
                  (process.env.productId || 'unpod.ai') as keyof typeof profiles
                ] || []
              )
                .slice(0, isDesktopApp ? 2 : 3)
                .map((profile, index) => (
                  <ProfileCard key={index} profile={profile} />
                ))}
            </StyledCardContainer>
            <Metrics />
          </StyledRoot>
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default Dashboard;
