'use client';

import { useEffect } from 'react';
import { useAuthActionsContext, useAuthContext } from '@unpod/providers';
import SubscriptionPlans from './Plans';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppPageHeader from '@unpod/components/common/AppPageHeader';
import { RiPriceTag2Line } from 'react-icons/ri';
import { StyledRoot } from '../index.styled';
import { useIntl } from 'react-intl';

const AppUpgradeModule = () => {
  const { isAuthenticated } = useAuthContext();
  const { getSubscription } = useAuthActionsContext();
  const { formatMessage } = useIntl();

  useEffect(() => {
    if (isAuthenticated) {
      getSubscription();
    }
  }, [isAuthenticated]);

  return (
    <>
      <AppPageHeader
        hideToggleBtn
        pageTitle={formatMessage({ id: 'upgrade.plan' })}
        titleIcon={<RiPriceTag2Line fontSize={21} />}
      />
      <AppPageContainer>
        <StyledRoot>
          <SubscriptionPlans />
        </StyledRoot>
      </AppPageContainer>
    </>
  );
};

export default AppUpgradeModule;
