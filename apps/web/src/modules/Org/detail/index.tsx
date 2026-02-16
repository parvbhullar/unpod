'use client';

import React, { Fragment, useEffect, useRef, useState } from 'react';
import { Button, Typography } from 'antd';
import clsx from 'clsx';
import {
  useAppContext,
  useAuthActionsContext,
  useAuthContext,
  useOrgContext,
} from '@unpod/providers';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';
import AppSpaceGrid from '@unpod/components/common/AppSpaceGrid';
import AppHubThreads from '@unpod/components/modules/AppHubThreads';
import PageHeader from './PageHeader';
import {
  StyledContainer,
  StyledInfoContainer,
  StyledNoAccessContainer,
  StyledNoAccessText,
  StyledSpaceContainer,
  StyledTabButtons,
  StyledTabContent,
} from './index.styled';
import AppAgentTypesWidget from '@unpod/components/modules/AppAgentTypesWidget';
import { HubSkeleton } from '@unpod/skeleton';

const { Title } = Typography;

const items = [
  {
    key: 'discover',
    label: 'Discover',
  },
  {
    key: 'spaces',
    label: 'Spaces',
  },
];

const ModuleHub = () => {
  const { listingType } = useAppContext();
  const { activeSpace } = useOrgContext();
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { isAuthenticated, user, isLoading, activeOrg } = useAuthContext();

  const [activeTab, setActiveTab] = useState('discover');
  const [isScrolled, setScrolled] = useState(false);
  const queryRef = useRef<{
    askQuery?: (values: Record<string, unknown>) => void;
  } | null>(null);

  useEffect(() => {
    window.addEventListener('scroll', function () {
      const scrollPos = window.scrollY;
      setScrolled(scrollPos > 50);
    });

    return () => {
      window.removeEventListener('scroll', function () {
        const scrollPos = window.scrollY;
        setScrolled(scrollPos > 50);
      });
    };
  }, []);

  useEffect(() => {
    if (activeOrg && isAuthenticated) {
      updateAuthUser({ ...user, active_organization: activeOrg });
      setActiveOrg(activeOrg);
    }
  }, [activeOrg, isAuthenticated]);

  return (
    <Fragment>
      <PageHeader
        isListingPage
        pageTitle={activeOrg?.name}
      />

      <AppPageContainer>
        {!isLoading ? (
          <>
            <StyledContainer $isScrolled={isScrolled}>
              <StyledInfoContainer>
                <Title level={2}>
                  {/*{user ? `Hello, ${user.first_name}` : 'Welcome Guest'}*/}
                  How can we assist you today?
                </Title>

                {/*<Title level={3} type="secondary">
                What are you looking for today?
              </Title>*/}
              </StyledInfoContainer>
              <AppQueryWindow
                ref={queryRef}
                pilotPopover
                defaultKbs={activeSpace?.slug ? [activeSpace.slug] : []}
              />

              <AppAgentTypesWidget />
            </StyledContainer>

            {activeOrg?.joined ? (
              <Fragment>
                <StyledTabButtons>
                  {items.map((item) => (
                    <Button
                      key={item.key}
                      type={item.key === activeTab ? 'primary' : 'default'}
                      shape="round"
                      onClick={() => setActiveTab(item.key)}
                    >
                      {item.label}
                    </Button>
                  ))}
                </StyledTabButtons>

                <StyledTabContent
                  className={clsx({ active: activeTab === 'spaces' })}
                >
                  <StyledSpaceContainer>
                    <AppSpaceGrid type="space" />
                  </StyledSpaceContainer>
                </StyledTabContent>

                <StyledTabContent
                  className={clsx({ active: activeTab === 'discover' })}
                >
                  <AppHubThreads
                    currentHub={activeOrg}
                    listingType={listingType}
                  />
                </StyledTabContent>
              </Fragment>
            ) : (
              <StyledNoAccessContainer>
                <StyledNoAccessText level={2}>
                  {"You Don't have Access to this Organization"}
                </StyledNoAccessText>
              </StyledNoAccessContainer>
            )}
          </>
        ) : (
          <HubSkeleton />
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default ModuleHub;
