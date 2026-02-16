'use client';

import { useEffect } from 'react';
import { useAuthActionsContext, useAuthContext } from '@unpod/providers';
import BillingDetail from './Detail';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppPageHeader from '@unpod/components/common/AppPageHeader';
import { StyledRoot } from './index.styled';
import { TbCalendarDollar } from 'react-icons/tb';
import { useRouter } from 'next/navigation';
import BillingSkeleton from '@unpod/skeleton/Billing';
import { useIntl } from 'react-intl';

const AppSubscription = () => {
  const { subscription, isAuthenticated } = useAuthContext();
  const router = useRouter();
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
        pageTitle={formatMessage({ id: 'billing.pageTitle' })}
        titleIcon={<TbCalendarDollar fontSize={21} />}
      />
      <AppPageContainer>
        <StyledRoot>
          {!subscription ? (
            <BillingSkeleton />
          ) : (
            <BillingDetail
              subscription={subscription}
              onChangePlan={() => router.push(`/billing/upgrade`)}
            />
          )}
        </StyledRoot>
      </AppPageContainer>
    </>
  );
};

export default AppSubscription;
